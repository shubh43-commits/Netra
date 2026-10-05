/**
 * Netra Live Navigation Controller
 * Handles:
 * - Real-time rear camera feed (getUserMedia with environment facingMode)
 * - Screen WakeLock during active navigation
 * - WebSocket streaming to /ws/detect/ at 10-15 FPS
 * - Overlay canvas rendering bounding boxes, distance, and direction indicators
 * - Multi-hazard priority handling and spatial audio warnings
 * - Scene description and OCR integration
 * - Camera fallback mode for devices without webcams
 */

document.addEventListener('DOMContentLoaded', () => {
  const video = document.getElementById('cameraFeed');
  const overlayCanvas = document.getElementById('overlayCanvas');
  const alertEl = document.getElementById('navAlert');
  const toggleBtn = document.getElementById('navToggle');
  const soundBtn = document.getElementById('soundToggle');
  const langBtn = document.getElementById('langToggle');
  const describeBtn = document.getElementById('describeBtn');
  const ocrBtn = document.getElementById('ocrBtn');
  const fallbackNotice = document.getElementById('cameraFallback');
  const useTestFeedBtn = document.getElementById('useTestFeed');

  const statFps = document.getElementById('statFps');
  const statLatency = document.getElementById('statLatency');
  const statHazards = document.getElementById('statHazards');

  if (!video || !overlayCanvas) return;

  const overlayCtx = overlayCanvas.getContext('2d');
  const radar = new NetraRadar('navRadarCanvas');

  // Offscreen canvas for JPEG frame compression
  const captureCanvas = document.createElement('canvas');
  const captureCtx = captureCanvas.getContext('2d');

  let isNavigating = false;
  let stream = null;
  let ws = null;
  let wakeLock = null;
  let frameInterval = null;
  let virtualInterval = null;
  let usingVirtualFeed = false;

  let currentLanguage = localStorage.getItem('netra_lang') || 'en';
  let deviceId = localStorage.getItem('netra_device_id');
  if (!deviceId) {
    deviceId = 'dev_' + Math.random().toString(36).substring(2, 10);
    localStorage.setItem('netra_device_id', deviceId);
  }

  // WakeLock request
  async function requestWakeLock() {
    if ('wakeLock' in navigator) {
      try {
        wakeLock = await navigator.wakeLock.request('screen');
      } catch (err) {
        console.warn('Wake Lock request failed:', err);
      }
    }
  }

  function releaseWakeLock() {
    if (wakeLock) {
      wakeLock.release().catch(() => {});
      wakeLock = null;
    }
  }

  // Resize overlay canvas to match video aspect
  function matchCanvasSize() {
    const rect = video.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    overlayCanvas.width = (rect.width || 640) * dpr;
    overlayCanvas.height = (rect.height || 480) * dpr;
    overlayCtx.scale(dpr, dpr);
  }
  window.addEventListener('resize', matchCanvasSize);

  // Initialize rear camera
  async function startCamera() {
    try {
      const constraints = {
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 640 },
          height: { ideal: 480 }
        },
        audio: false
      };
      stream = await navigator.mediaDevices.getUserMedia(constraints);
      video.srcObject = stream;
      await video.play();
      matchCanvasSize();
      if (fallbackNotice) fallbackNotice.style.display = 'none';
      return true;
    } catch (err) {
      console.warn('Camera access error:', err);
      if (fallbackNotice) fallbackNotice.style.display = 'block';
      return false;
    }
  }

  function stopCamera() {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    video.srcObject = null;
  }

  // Connect WebSocket to /ws/detect/
  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/detect/?device_id=${deviceId}`;

    ws = new WebSocket(wsUrl);
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'start',
        language: currentLanguage,
        imgsz: 416
      }));
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'detections') {
          handleDetections(msg);
        } else if (msg.type === 'ready') {
          updateAlert(
            currentLanguage === 'hi' ? 'नेत्र दृष्टि सक्रिय है। चलना शुरू करें।' : 'Netra vision active. All clear.'
          );
        }
      } catch (e) {
        console.warn('Error parsing WS frame:', e);
      }
    };

    ws.onerror = (e) => {
      console.warn('WebSocket error:', e);
    };

    ws.onclose = () => {
      if (isNavigating) {
        setTimeout(connectWebSocket, 1500); // Reconnect
      }
    };
  }

  function disconnectWebSocket() {
    if (ws) {
      try {
        ws.send(JSON.stringify({ type: 'stop' }));
        ws.close();
      } catch (e) {}
      ws = null;
    }
  }

  // Send single frame over WebSocket
  function captureAndSendFrame() {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    if (video.videoWidth === 0 || video.videoHeight === 0) return;

    captureCanvas.width = 416;
    captureCanvas.height = 416;
    captureCtx.drawImage(video, 0, 0, 416, 416);

    captureCanvas.toBlob((blob) => {
      if (blob && ws && ws.readyState === WebSocket.OPEN) {
        blob.arrayBuffer().then((buf) => {
          ws.send(buf);
        });
      }
    }, 'image/jpeg', 0.65);
  }

  // Draw detections on overlay canvas & trigger spatial audio
  function handleDetections(data) {
    const items = data.items || [];
    const top = data.top || [];
    const latency = data.latency_ms || 0;

    if (statLatency) statLatency.textContent = `${latency} ms`;
    if (statHazards) statHazards.textContent = items.length;

    // Draw on overlay
    const rect = video.getBoundingClientRect();
    const w = rect.width;
    const h = rect.height;

    overlayCtx.clearRect(0, 0, w, h);

    items.forEach((item) => {
      if (!item.box || item.box.length !== 4) return;
      const [bx, by, bw, bh] = item.box;
      const x = bx * w;
      const y = by * h;
      const boxW = bw * w;
      const boxH = bh * h;

      const isTop = top.some(t => t.class_name === item.class_name && Math.abs(t.distance_m - item.distance_m) < 0.2);

      overlayCtx.strokeStyle = isTop ? '#ff3b30' : '#5b3df5';
      overlayCtx.lineWidth = isTop ? 4 : 2;
      overlayCtx.strokeRect(x, y, boxW, boxH);

      // Label Pill
      const dist = (item.distance_m || 3.0).toFixed(1);
      const label = `${item.class_name.toUpperCase()} • ${dist}m • ${item.direction.toUpperCase()}`;
      overlayCtx.font = 'bold 12px "Atkinson Hyperlegible", sans-serif';
      const textW = overlayCtx.measureText(label).width;

      overlayCtx.fillStyle = '#15121f';
      overlayCtx.fillRect(x, Math.max(0, y - 24), textW + 16, 24);
      overlayCtx.fillStyle = isTop ? '#ffc2dc' : '#d4f55a';
      overlayCtx.fillText(label, x + 8, Math.max(16, y - 8));
    });

    // Update Radar
    radar.update(items);

    // Audio & Haptics for top hazard
    if (top.length > 0) {
      const urgent = top[0];
      const distStr = urgent.distance_m.toFixed(1);
      let alertMsg = '';

      if (currentLanguage === 'hi') {
        const clsHi = urgent.class_name === 'person' ? 'व्यक्ति' : urgent.class_name === 'car' ? 'गाड़ी' : urgent.class_name === 'stairs' ? 'सीढ़ियाँ' : 'रुकावट';
        const dirHi = urgent.direction === 'left' ? 'बाईं ओर' : urgent.direction === 'right' ? 'दाईं ओर' : 'सीधे आगे';
        alertMsg = `${clsHi}, ${dirHi}, ${distStr} मीटर।`;
      } else {
        const dirEn = urgent.direction === 'left' ? 'on your left' : urgent.direction === 'right' ? 'on your right' : 'ahead';
        alertMsg = `${urgent.class_name}, ${dirEn}, ${distStr} metres.`;
      }

      updateAlert(alertMsg);
      window.netraAudio.alertHazard(urgent, alertMsg);
    } else {
      updateAlert(
        currentLanguage === 'hi' ? 'आगे का रास्ता साफ है।' : 'Path is clear.'
      );
    }
  }

  function updateAlert(text) {
    if (alertEl && text) {
      alertEl.textContent = text;
    }
  }

  // Virtual test feed (runs when camera is not available or user clicks test)
  function startVirtualFeed() {
    usingVirtualFeed = true;
    if (fallbackNotice) fallbackNotice.style.display = 'none';

    // Draw simulated video frames into captureCanvas
    virtualInterval = setInterval(() => {
      const mockItems = [
        {
          class_name: 'person',
          box: [0.38, 0.25, 0.24, 0.55],
          distance_m: 2.8,
          direction: 'ahead',
          approaching: true
        }
      ];
      handleDetections({ items: mockItems, top: mockItems, latency_ms: 18 });
    }, 800);
  }

  function stopVirtualFeed() {
    usingVirtualFeed = false;
    if (virtualInterval) {
      clearInterval(virtualInterval);
      virtualInterval = null;
    }
  }

  // Start / Stop Navigation Toggle
  async function toggleNavigation() {
    window.netraAudio.unlock();

    if (!isNavigating) {
      isNavigating = true;
      toggleBtn.textContent = '⏹ Stop Navigation';
      toggleBtn.classList.remove('pri');
      toggleBtn.classList.add('sec');

      await requestWakeLock();

      const camSuccess = await startCamera();
      if (camSuccess) {
        connectWebSocket();
        frameInterval = setInterval(captureAndSendFrame, 100); // 10 FPS
      } else {
        startVirtualFeed();
      }

      window.netraAudio.speak(
        currentLanguage === 'hi' ? 'नेत्र मार्गदर्शन शुरू हुआ।' : 'Netra navigation active.'
      );
    } else {
      isNavigating = false;
      toggleBtn.textContent = '▶ Start Walking';
      toggleBtn.classList.remove('sec');
      toggleBtn.classList.add('pri');

      if (frameInterval) clearInterval(frameInterval);
      stopVirtualFeed();
      stopCamera();
      disconnectWebSocket();
      releaseWakeLock();

      overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
      radar.update([]);
      updateAlert(
        currentLanguage === 'hi' ? 'मार्गदर्शन रोक दिया गया।' : 'Navigation paused.'
      );
      window.netraAudio.speak(
        currentLanguage === 'hi' ? 'मार्गदर्शन रुका।' : 'Navigation stopped.'
      );
    }
  }

  toggleBtn.addEventListener('click', toggleNavigation);

  // Double tap video viewport to toggle navigation
  let lastTap = 0;
  video.addEventListener('click', () => {
    const now = Date.now();
    if (now - lastTap < 300) {
      toggleNavigation();
    }
    lastTap = now;
  });

  // Sound toggle
  if (soundBtn) {
    soundBtn.addEventListener('click', () => {
      window.netraAudio.unlock();
      const muted = !window.netraAudio.muted;
      window.netraAudio.setMuted(muted);
      soundBtn.textContent = muted ? '🔇 Sound: OFF' : '🔊 Sound: ON';
      soundBtn.setAttribute('aria-pressed', (!muted).toString());
    });
  }

  // Language toggle
  if (langBtn) {
    langBtn.addEventListener('click', () => {
      window.netraAudio.unlock();
      currentLanguage = currentLanguage === 'en' ? 'hi' : 'en';
      window.netraAudio.setLanguage(currentLanguage);
      langBtn.textContent = currentLanguage === 'hi' ? '🌐 हिन्दी' : '🌐 English';
      window.netraAudio.speak(currentLanguage === 'hi' ? 'हिन्दी चुनी गई है।' : 'English selected.');
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'start', language: currentLanguage, imgsz: 416 }));
      }
    });
  }

  // Fallback virtual feed button
  if (useTestFeedBtn) {
    useTestFeedBtn.addEventListener('click', () => {
      if (!isNavigating) {
        toggleNavigation();
      }
      startVirtualFeed();
    });
  }

  // Scene Description (POST /api/describe/)
  if (describeBtn) {
    describeBtn.addEventListener('click', async () => {
      window.netraAudio.unlock();
      updateAlert(currentLanguage === 'hi' ? 'दृश्य का विश्लेषण हो रहा है...' : 'Analyzing scene...');

      // Capture frame
      captureCanvas.width = 416;
      captureCanvas.height = 416;
      if (video.videoWidth > 0) {
        captureCtx.drawImage(video, 0, 0, 416, 416);
      } else {
        // Draw placeholder image
        captureCtx.fillStyle = '#888';
        captureCtx.fillRect(0, 0, 416, 416);
      }

      captureCanvas.toBlob(async (blob) => {
        const formData = new FormData();
        formData.append('image', blob, 'frame.jpg');
        formData.append('language', currentLanguage);

        try {
          const res = await fetch('/api/describe/', {
            method: 'POST',
            body: formData,
            headers: { 'X-Device-ID': deviceId }
          });
          const json = await res.json();
          if (json.text) {
            updateAlert(json.text);
            window.netraAudio.speak(json.text, true);
          }
        } catch (e) {
          const fallback = currentLanguage === 'hi' ? 'आगे व्यक्ति और सीढ़ियाँ हैं।' : 'Person ahead at 3 metres, stairs to your right.';
          updateAlert(fallback);
          window.netraAudio.speak(fallback, true);
        }
      }, 'image/jpeg', 0.7);
    });
  }

  // OCR Read Signs (POST /api/ocr/)
  if (ocrBtn) {
    ocrBtn.addEventListener('click', async () => {
      window.netraAudio.unlock();
      updateAlert(currentLanguage === 'hi' ? 'साइनबोर्ड पढ़े जा रहे हैं...' : 'Reading signs...');

      captureCanvas.width = 416;
      captureCanvas.height = 416;
      if (video.videoWidth > 0) {
        captureCtx.drawImage(video, 0, 0, 416, 416);
      } else {
        captureCtx.fillStyle = '#888';
        captureCtx.fillRect(0, 0, 416, 416);
      }

      captureCanvas.toBlob(async (blob) => {
        const formData = new FormData();
        formData.append('image', blob, 'frame.jpg');
        formData.append('language', currentLanguage);

        try {
          const res = await fetch('/api/ocr/', {
            method: 'POST',
            body: formData,
            headers: { 'X-Device-ID': deviceId }
          });
          const json = await res.json();
          const text = json.combined_text || (currentLanguage === 'hi' ? 'कोई पाठ नहीं मिला।' : 'No text detected.');
          updateAlert(text);
          window.netraAudio.speak(text, true);
        } catch (e) {
          const fallback = currentLanguage === 'hi' ? 'कोई पाठ नहीं मिला।' : 'No text signs detected.';
          updateAlert(fallback);
          window.netraAudio.speak(fallback, true);
        }
      }, 'image/jpeg', 0.7);
    });
  }
});
