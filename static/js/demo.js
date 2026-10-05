/**
 * Netra Interactive Street Simulator
 * Allows users to test spatial sound, speech announcements, and radar tracking
 * without needing a webcam or physical street environment.
 */

document.addEventListener('DOMContentLoaded', () => {
  const streetCanvas = document.getElementById('streetCanvas');
  const radarCanvas = document.getElementById('radarCanvas');
  const alertEl = document.getElementById('demoAlert');
  const toggleBtn = document.getElementById('simToggle');
  const soundBtn = document.getElementById('soundToggle');
  const langBtn = document.getElementById('simLang');
  const describeBtn = document.getElementById('describeBtn');

  const statFps = document.getElementById('statFps');
  const statHazards = document.getElementById('statHazards');
  const statDistance = document.getElementById('statDistance');

  if (!streetCanvas) return;

  const ctx = streetCanvas.getContext('2d');
  const radar = new NetraRadar('radarCanvas');

  let running = false;
  let lastFrameTime = performance.now();
  let frameCount = 0;
  let fps = 0;
  let lastFpsCalc = performance.now();

  // Traffic light state
  let trafficLightColor = 'green'; // 'green' or 'red'

  // Simulated active obstacles
  let obstacles = [
    { id: 1, class_name: 'person', distance_m: 4.5, direction: 'ahead', approaching: true, speed: 0.03, x: 0.5, y: 0.5 },
    { id: 2, class_name: 'car', distance_m: 6.8, direction: 'left', approaching: true, speed: 0.06, x: 0.25, y: 0.6 }
  ];

  let beepCooldown = 0;

  function resizeCanvas() {
    const rect = streetCanvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    streetCanvas.width = rect.width * dpr;
    streetCanvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
  }
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  function announceHazard(item) {
    if (!item) return;
    const lang = window.netraAudio.language;
    let spoken = '';

    if (lang === 'hi') {
      const clsHi = item.class_name === 'person' ? 'व्यक्ति' : item.class_name === 'car' ? 'गाड़ी' : item.class_name === 'stairs' ? 'सीढ़ियाँ' : 'रुकावट';
      const dirHi = item.direction === 'left' ? 'बाईं ओर' : item.direction === 'right' ? 'दाईं ओर' : 'सीधे आगे';
      spoken = `${clsHi}, ${dirHi}, ${item.distance_m.toFixed(1)} मीटर।`;
    } else {
      const dirEn = item.direction === 'left' ? 'on your left' : item.direction === 'right' ? 'on your right' : 'ahead';
      spoken = `${item.class_name}, ${dirEn}, ${item.distance_m.toFixed(1)} metres.`;
    }

    if (alertEl) {
      alertEl.textContent = spoken;
    }

    window.netraAudio.alertHazard(item, spoken);
  }

  // Simulation physics loop
  function updateSimulation() {
    if (!running) return;

    // Move obstacles closer
    obstacles.forEach((ob) => {
      ob.distance_m -= ob.speed;
      if (ob.distance_m < 0.6) {
        ob.distance_m = 7.5; // Reset back to distance
      }

      // Update direction and x coordinate
      if (ob.direction === 'left') {
        ob.x = 0.22 - (7.5 - ob.distance_m) * 0.015;
      } else if (ob.direction === 'right') {
        ob.x = 0.78 + (7.5 - ob.distance_m) * 0.015;
      } else {
        ob.x = 0.5;
      }
    });

    // Find top hazard
    let topHazard = null;
    let minDist = 999;
    obstacles.forEach((ob) => {
      if (ob.distance_m < minDist) {
        minDist = ob.distance_m;
        topHazard = ob;
      }
    });

    // Beep interval calculation (closer = more frequent)
    beepCooldown++;
    const intervalThreshold = Math.max(12, Math.floor(minDist * 10));
    if (beepCooldown >= intervalThreshold && topHazard) {
      window.netraAudio.playProximityBeep(topHazard.direction, topHazard.distance_m);
      beepCooldown = 0;
    }

    // Update stats
    if (statHazards) statHazards.textContent = obstacles.length;
    if (statDistance) statDistance.textContent = topHazard ? `${topHazard.distance_m.toFixed(1)}m` : '--';
  }

  // Render street scene
  function renderScene() {
    const w = streetCanvas.getBoundingClientRect().width;
    const h = streetCanvas.getBoundingClientRect().height;

    ctx.clearRect(0, 0, w, h);

    // Sky & Background
    ctx.fillStyle = '#c6e6ff';
    ctx.fillRect(0, 0, w, h * 0.45);

    // Ground / Street
    ctx.fillStyle = '#e8decb';
    ctx.fillRect(0, h * 0.45, w, h * 0.55);

    // Perspective road
    ctx.beginPath();
    ctx.moveTo(w * 0.38, h * 0.45);
    ctx.lineTo(w * 0.62, h * 0.45);
    ctx.lineTo(w * 0.88, h);
    ctx.lineTo(w * 0.12, h);
    ctx.closePath();
    ctx.fillStyle = '#39334a';
    ctx.fill();

    // Center dashed lane line
    ctx.strokeStyle = '#ffd9b8';
    ctx.lineWidth = 4;
    ctx.setLineDash([16, 16]);
    ctx.beginPath();
    ctx.moveTo(w * 0.5, h * 0.45);
    ctx.lineTo(w * 0.5, h);
    ctx.stroke();
    ctx.setLineDash([]);

    // Sidewalks
    ctx.fillStyle = '#f5efe6';
    // Left sidewalk
    ctx.beginPath();
    ctx.moveTo(0, h * 0.45);
    ctx.lineTo(w * 0.38, h * 0.45);
    ctx.lineTo(w * 0.12, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = '#15121f';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Right sidewalk
    ctx.beginPath();
    ctx.moveTo(w, h * 0.45);
    ctx.lineTo(w * 0.62, h * 0.45);
    ctx.lineTo(w * 0.88, h);
    ctx.lineTo(w, h);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Traffic light post on right sidewalk
    const tlX = w * 0.78;
    const tlY = h * 0.32;
    ctx.fillStyle = '#15121f';
    ctx.fillRect(tlX - 3, tlY, 6, 70);
    ctx.fillStyle = '#222';
    ctx.fillRect(tlX - 12, tlY - 42, 24, 46);
    // Red lamp
    ctx.beginPath();
    ctx.arc(tlX, tlY - 30, 7, 0, Math.PI * 2);
    ctx.fillStyle = trafficLightColor === 'red' ? '#ff3b30' : '#441111';
    ctx.fill();
    // Green lamp
    ctx.beginPath();
    ctx.arc(tlX, tlY - 10, 7, 0, Math.PI * 2);
    ctx.fillStyle = trafficLightColor === 'green' ? '#34c759' : '#113311';
    ctx.fill();

    // Render obstacles on canvas with bounding boxes
    obstacles.forEach((ob) => {
      // Perspective scale based on distance (7.5m -> 0.3x, 1m -> 1.0x)
      const scale = Math.max(0.25, 1.2 - (ob.distance_m / 8.0));
      const boxW = 80 * scale;
      const boxH = 130 * scale;
      const obX = ob.x * w;
      const obY = h * 0.45 + (1.0 - (ob.distance_m / 8.0)) * (h * 0.5);

      // Draw obstacle icon / avatar
      ctx.save();
      ctx.translate(obX, obY);

      if (ob.class_name === 'person') {
        // Pedestrian silhouette
        ctx.fillStyle = '#3db8ff';
        ctx.beginPath();
        ctx.arc(0, -boxH * 0.75, 12 * scale, 0, Math.PI * 2); // Head
        ctx.fill();
        ctx.strokeStyle = '#15121f';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.fillStyle = '#5b3df5';
        ctx.fillRect(-14 * scale, -boxH * 0.6, 28 * scale, 42 * scale); // Torso
        ctx.strokeRect(-14 * scale, -boxH * 0.6, 28 * scale, 42 * scale);
      } else if (ob.class_name === 'car') {
        // Car box
        ctx.fillStyle = '#ff7ab6';
        ctx.fillRect(-boxW * 0.5, -boxH * 0.5, boxW, boxH * 0.6);
        ctx.strokeStyle = '#15121f';
        ctx.lineWidth = 2;
        ctx.strokeRect(-boxW * 0.5, -boxH * 0.5, boxW, boxH * 0.6);
        // Headlights
        ctx.fillStyle = '#ffd9b8';
        ctx.fillRect(-boxW * 0.4, -boxH * 0.1, 14 * scale, 8 * scale);
        ctx.fillRect(boxW * 0.4 - 14 * scale, -boxH * 0.1, 14 * scale, 8 * scale);
      } else if (ob.class_name === 'stairs') {
        // Stairs
        ctx.fillStyle = '#ffc2dc';
        for (let s = 0; s < 3; s++) {
          ctx.fillRect(-boxW * 0.4 + s * 8 * scale, -boxH * 0.3 + s * 14 * scale, boxW * 0.8 - s * 16 * scale, 12 * scale);
          ctx.strokeRect(-boxW * 0.4 + s * 8 * scale, -boxH * 0.3 + s * 14 * scale, boxW * 0.8 - s * 16 * scale, 12 * scale);
        }
      }

      // Netra Bounding Box & Badge
      ctx.strokeStyle = ob.approaching ? '#ff3b30' : '#5b3df5';
      ctx.lineWidth = 3;
      ctx.strokeRect(-boxW * 0.6, -boxH * 0.85, boxW * 1.2, boxH);

      // Tactile Label Pill
      const labelText = `${ob.class_name.toUpperCase()} • ${ob.distance_m.toFixed(1)}m`;
      ctx.font = 'bold 12px "Atkinson Hyperlegible", sans-serif';
      const textMetrics = ctx.measureText(labelText);
      const pillW = textMetrics.width + 16;
      const pillH = 22;

      ctx.fillStyle = '#15121f';
      ctx.fillRect(-pillW / 2, -boxH * 0.85 - pillH - 4, pillW, pillH);
      ctx.fillStyle = '#d4f55a';
      ctx.fillText(labelText, -pillW / 2 + 8, -boxH * 0.85 - 8);

      ctx.restore();
    });

    // Update Radar
    radar.update(obstacles);
  }

  // Animation Loop
  function tick(timestamp) {
    frameCount++;
    if (timestamp - lastFpsCalc >= 1000) {
      fps = frameCount;
      frameCount = 0;
      lastFpsCalc = timestamp;
      if (statFps) statFps.textContent = `${fps} FPS`;
    }

    updateSimulation();
    renderScene();

    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);

  // Toggle Play / Pause
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      window.netraAudio.unlock();
      running = !running;
      toggleBtn.textContent = running ? '⏸ Pause Simulator' : '▶ Start Walking Simulator';
      toggleBtn.classList.toggle('pri', !running);
      toggleBtn.classList.toggle('sec', running);

      if (running) {
        window.netraAudio.speak(
          window.netraAudio.language === 'hi' ? 'सिमुलेशन शुरू हुआ। सड़क खुली है।' : 'Simulation started. Street is active.'
        );
      }
    });
  }

  // Mute / Unmute
  if (soundBtn) {
    soundBtn.addEventListener('click', () => {
      window.netraAudio.unlock();
      const muted = !window.netraAudio.muted;
      window.netraAudio.setMuted(muted);
      soundBtn.textContent = muted ? '🔇 Unmute Audio' : '🔊 Sound: ON';
      soundBtn.setAttribute('aria-pressed', (!muted).toString());
    });
  }

  // Language Switch
  if (langBtn) {
    langBtn.addEventListener('click', () => {
      window.netraAudio.unlock();
      const current = window.netraAudio.language;
      const nextLang = current === 'en' ? 'hi' : 'en';
      window.netraAudio.setLanguage(nextLang);
      langBtn.textContent = nextLang === 'hi' ? '🌐 Language: हिन्दी' : '🌐 Language: English';
      window.netraAudio.speak(nextLang === 'hi' ? 'हिन्दी चुनी गई है।' : 'English selected.');
    });
  }

  // Interactive buttons to spawn / test specific hazards immediately
  document.querySelectorAll('[data-spawn]').forEach((btn) => {
    btn.addEventListener('click', () => {
      window.netraAudio.unlock();
      const type = btn.getAttribute('data-spawn');

      if (type === 'person') {
        const item = { id: Date.now(), class_name: 'person', distance_m: 3.0, direction: 'ahead', approaching: true, speed: 0.04, x: 0.5, y: 0.5 };
        obstacles = [item];
        announceHazard(item);
      } else if (type === 'car') {
        const item = { id: Date.now(), class_name: 'car', distance_m: 5.2, direction: 'left', approaching: true, speed: 0.08, x: 0.22, y: 0.6 };
        obstacles = [item];
        announceHazard(item);
      } else if (type === 'stairs') {
        const item = { id: Date.now(), class_name: 'stairs', distance_m: 2.1, direction: 'right', approaching: false, speed: 0, x: 0.8, y: 0.7 };
        obstacles = [item];
        announceHazard(item);
      } else if (type === 'light') {
        trafficLightColor = trafficLightColor === 'green' ? 'red' : 'green';
        const msg = trafficLightColor === 'green'
          ? (window.netraAudio.language === 'hi' ? 'हरी बत्ती। आप जा सकते हैं।' : 'Green light. You can cross safely.')
          : (window.netraAudio.language === 'hi' ? 'लाल बत्ती। कृपया रुकें।' : 'Red light. Stop and wait.');
        if (alertEl) alertEl.textContent = msg;
        window.netraAudio.speak(msg, true);
        window.netraAudio.vibrate(trafficLightColor === 'red' ? 'critical' : 'tap');
      }
    });
  });

  // Test Directional Panning Beeps
  document.querySelectorAll('[data-test-beep]').forEach((btn) => {
    btn.addEventListener('click', () => {
      window.netraAudio.unlock();
      const dir = btn.getAttribute('data-test-beep');
      window.netraAudio.playProximityBeep(dir, 2.5, 0.2);
      if (alertEl) {
        alertEl.textContent = `Beep played on ${dir.toUpperCase()} channel.`;
      }
    });
  });

  // Scene Description
  if (describeBtn) {
    describeBtn.addEventListener('click', () => {
      window.netraAudio.unlock();
      const count = obstacles.length;
      const lang = window.netraAudio.language;
      let text = '';
      if (count === 0) {
        text = lang === 'hi' ? 'आगे का रास्ता पूरी तरह साफ है।' : 'The road ahead is completely clear.';
      } else {
        const top = obstacles[0];
        if (lang === 'hi') {
          text = `आपके सामने ${top.class_name === 'person' ? 'एक व्यक्ति' : top.class_name === 'car' ? 'एक गाड़ी' : 'रुकावट'} ${top.distance_m.toFixed(1)} मीटर पर है। ट्रैफ़िक लाइट ${trafficLightColor === 'green' ? 'हरी' : 'लाल'} है।`;
        } else {
          text = `There is a ${top.class_name} ${top.direction} at ${top.distance_m.toFixed(1)} metres. Traffic light is ${trafficLightColor}.`;
        }
      }

      if (alertEl) alertEl.textContent = text;
      window.netraAudio.speak(text, true);
    });
  }
});
