"""
Integration tests for Netra Detection WebSocket (/ws/detect/).
Verifies:
- Async handshake and start / ready sequence
- Ping / pong liveness check
- Frame validation (magic bytes, max 300KB)
- 15 FPS rate limiting
- Thread-safe non-blocking inference and top hazards
- Per-device concurrent connection limit
"""
import io
import time
import asyncio
import pytest
from PIL import Image
from channels.testing import WebsocketCommunicator

from config.asgi import application
from apps.detection.services.inference import InferenceService


@pytest.mark.asyncio
async def test_websocket_lifecycle():
    communicator = WebsocketCommunicator(application, "/ws/detect/?device_id=test_dev_life")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed to establish."

    try:
        # 1. Ping / Pong
        await communicator.send_json_to({"type": "ping"})
        res = await communicator.receive_json_from()
        assert res["type"] == "pong"
        assert "timestamp" in res

        # Generate a small valid JPEG
        img = Image.new("RGB", (64, 64), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        jpeg_bytes = buf.getvalue()

        # 2. Binary frame before start -> error 'not_started'
        await communicator.send_to(bytes_data=jpeg_bytes)
        res = await communicator.receive_json_from()
        assert res["type"] == "error"
        assert res["code"] == "not_started"

        # 3. Start session
        await communicator.send_json_to({"type": "start", "language": "en", "imgsz": 416})
        res = await communicator.receive_json_from()
        assert res["type"] == "ready"
        assert res["session_active"] is True

        # 4. Invalid JPEG magic bytes
        await communicator.send_to(bytes_data=b"INVALID_MAGIC_HEADER_BYTES")
        res = await communicator.receive_json_from()
        assert res["type"] == "error"
        assert res["code"] == "invalid_jpeg"

        # 5. Frame exceeding 300 KB limit
        oversized = b"\xff\xd8\xff" + b"\x00" * (300 * 1024 + 100)
        await communicator.send_to(bytes_data=oversized)
        res = await communicator.receive_json_from()
        assert res["type"] == "error"
        assert res["code"] == "frame_too_large"

        # 6. Valid JPEG inference with mock model
        inference = InferenceService.get_instance()
        def mock_predict(img_data, imgsz=416, conf=0.35):
            return [{
                "class_name": "person",
                "confidence": 0.91,
                "box": [0.4, 0.3, 0.2, 0.5],
                "distance_m": 2.2,
                "direction": "ahead",
                "approaching": True,
            }]
        inference.set_mock_model(mock_predict)

        # Wait past rate limit window (> 0.067s)
        await asyncio.sleep(0.1)
        await communicator.send_to(bytes_data=jpeg_bytes)
        res = await communicator.receive_json_from()
        assert res["type"] == "detections"
        assert res["frame_id"] == 1
        assert len(res["items"]) == 1
        assert res["items"][0]["class_name"] == "person"
        assert len(res["top"]) == 1
        assert res["top"][0]["class_name"] == "person"
        assert "latency_ms" in res

        # 7. Rate limit drops frame if sent too quickly (< 1/15s)
        await communicator.send_to(bytes_data=jpeg_bytes)
        res = await communicator.receive_json_from()
        assert res["type"] == "dropped"
        assert res["reason"] == "rate_limit_exceeded"

        # 8. Stop session
        await communicator.send_json_to({"type": "stop"})
        res = await communicator.receive_json_from()
        assert res["type"] == "stopped"

    finally:
        InferenceService.get_instance().set_mock_model(None)
        await communicator.disconnect()


@pytest.mark.asyncio
async def test_websocket_device_concurrency_limit():
    dev_id = "test_dev_concurrency_guard"
    comm1 = WebsocketCommunicator(application, f"/ws/detect/?device_id={dev_id}")
    c1, _ = await comm1.connect()
    assert c1

    comm2 = WebsocketCommunicator(application, f"/ws/detect/?device_id={dev_id}")
    c2, _ = await comm2.connect()
    assert c2

    # Third concurrent connection on same device ID should be rejected
    comm3 = WebsocketCommunicator(application, f"/ws/detect/?device_id={dev_id}")
    c3, code = await comm3.connect()
    assert not c3 or code == 4003

    await comm1.disconnect()
    await comm2.disconnect()
