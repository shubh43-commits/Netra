"""
Channels WebSocket Consumer for real-time camera inference: /ws/detect/
Implements:
- Protocol with JSON control frames ('start', 'ready', 'ping', 'stop') and binary JPEG frames
- Max 300 KB frame size limit
- 15 FPS rate limiting per connection
- In-memory JPEG magic-byte validation (b'\\xff\\xd8\\xff')
- Per-device connection limits
- Object tracking and top-hazard ranking without disk persistence
"""
import time
import json
import asyncio
from typing import Dict, Any, ClassVar
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer

from .services.inference import InferenceService
from .services.tracker import StreamTracker
from .services.priority import select_top_hazards

MAX_FRAME_BYTES: int = 300 * 1024  # 300 KB
MAX_FPS: float = 15.0
MIN_FRAME_INTERVAL: float = 1.0 / MAX_FPS  # ~0.0667 seconds
IDLE_TIMEOUT_SECONDS: float = 120.0  # 2 minutes of silence
MAX_CONNECTIONS_PER_DEVICE: int = 2


class DetectionConsumer(AsyncWebsocketConsumer):
    """
    Asynchronous WebSocket Consumer handling continuous camera inference.
    """
    # Tracks active connection counts per device ID
    _device_connections: ClassVar[Dict[str, int]] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_id: str = "anonymous"
        self.session_started: bool = False
        self.language: str = "en"
        self.imgsz: int = 416
        self.frame_counter: int = 0
        self.last_frame_time: float = 0.0
        self.last_activity_time: float = time.time()
        self.tracker = StreamTracker()
        self.idle_check_task: asyncio.Task = None

    async def connect(self) -> None:
        # Extract device_id from query params or headers
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        device_ids = params.get("device_id", [])
        if device_ids:
            self.device_id = device_ids[0].strip()

        # Enforce connection limit per device
        current_conns = self._device_connections.get(self.device_id, 0)
        if current_conns >= MAX_CONNECTIONS_PER_DEVICE:
            await self.close(code=4003)
            return

        self._device_connections[self.device_id] = current_conns + 1
        await self.accept()

        # Launch background task to monitor idle timeout
        self.idle_check_task = asyncio.create_task(self._idle_monitor())

    async def disconnect(self, close_code: int) -> None:
        # Decrement device connection count
        if self.device_id in self._device_connections:
            self._device_connections[self.device_id] = max(
                0, self._device_connections[self.device_id] - 1
            )
            if self._device_connections[self.device_id] == 0:
                del self._device_connections[self.device_id]

        if self.idle_check_task and not self.idle_check_task.done():
            self.idle_check_task.cancel()

    async def _idle_monitor(self) -> None:
        """
        Closes dormant connections that exceed idle timeout to release server memory.
        """
        try:
            while True:
                await asyncio.sleep(15.0)
                if (time.time() - self.last_activity_time) > IDLE_TIMEOUT_SECONDS:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "code": "idle_timeout",
                        "message": "Connection closed due to inactivity."
                    }))
                    await self.close(code=4008)
                    break
        except asyncio.CancelledError:
            pass

    async def receive(self, text_data: str = None, bytes_data: bytes = None) -> None:
        self.last_activity_time = time.time()

        # ----------------------------------------------------------------------
        # 1. JSON Text Control Frames
        # ----------------------------------------------------------------------
        if text_data:
            try:
                payload = json.loads(text_data)
            except Exception:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "code": "malformed_json",
                    "message": "Control frame must be valid JSON."
                }))
                return

            msg_type = payload.get("type")

            if msg_type == "start":
                self.session_started = True
                self.language = payload.get("language", "en")
                self.imgsz = int(payload.get("imgsz", 416))
                await self.send(text_data=json.dumps({
                    "type": "ready",
                    "session_active": True,
                    "language": self.language,
                    "imgsz": self.imgsz
                }))

            elif msg_type == "ping":
                await self.send(text_data=json.dumps({
                    "type": "pong",
                    "timestamp": time.time()
                }))

            elif msg_type == "stop":
                self.session_started = False
                await self.send(text_data=json.dumps({
                    "type": "stopped",
                    "session_active": False
                }))

            else:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": f"Unknown message type '{msg_type}'."
                }))
            return

        # ----------------------------------------------------------------------
        # 2. Binary JPEG Video Frames
        # ----------------------------------------------------------------------
        if bytes_data:
            if not self.session_started:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "code": "not_started",
                    "message": "Stream not active. Send {'type': 'start'} first."
                }))
                return

            # Frame size validation (max 300 KB)
            if len(bytes_data) > MAX_FRAME_BYTES:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "code": "frame_too_large",
                    "message": f"Frame size ({len(bytes_data)} bytes) exceeds 300 KB limit."
                }))
                return

            # JPEG Magic bytes validation: starts with \xff\xd8\xff
            if len(bytes_data) < 3 or bytes_data[:3] != b'\xff\xd8\xff':
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "code": "invalid_jpeg",
                    "message": "Binary payload is not a valid JPEG image."
                }))
                return

            # Rate limiting: max 15 FPS per connection
            now = time.time()
            if (now - self.last_frame_time) < MIN_FRAME_INTERVAL:
                await self.send(text_data=json.dumps({
                    "type": "dropped",
                    "reason": "rate_limit_exceeded",
                    "max_fps": MAX_FPS
                }))
                return

            self.last_frame_time = now
            self.frame_counter += 1
            frame_id = self.frame_counter
            start_t = time.perf_counter()

            # Execute computer vision inference in non-blocking thread pool
            try:
                loop = asyncio.get_running_loop()
                inference = InferenceService.get_instance()

                # Process strictly in memory
                raw_detections = await loop.run_in_executor(
                    None,
                    inference.decode_and_predict,
                    bytes_data,
                    self.imgsz,
                    0.35
                )

                # Track approach velocity and persistence
                tracked_detections = self.tracker.update(raw_detections)

                # Prioritize top 2 hazards
                top_hazards = select_top_hazards(tracked_detections, limit=2)

                latency_ms = round((time.perf_counter() - start_t) * 1000, 1)

                await self.send(text_data=json.dumps({
                    "type": "detections",
                    "frame_id": frame_id,
                    "items": tracked_detections,
                    "top": top_hazards,
                    "latency_ms": latency_ms
                }))

            except Exception as e:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "code": "inference_failure",
                    "message": str(e)
                }))
