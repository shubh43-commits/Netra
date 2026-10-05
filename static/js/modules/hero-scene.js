/**
 * Blind Assist Navigator - 3D Spatial Hero Scene (Three.js Rebuilt Edition)
 * 
 * Features:
 * - Ultra-sleek glowing titanium smartphone with live animated radar HUD screen canvas.
 * - Volumetric holographic sweeping radar cone with ground projection fan.
 * - Floating 3D holographic markers with text badges: Person (Emerald), Car (Amber), Stairs (Violet).
 * - Drifting 3D LiDAR point cloud particles representing spatial depth mapping.
 * - Damped mouse/pointer & device tilt parallax.
 * - IntersectionObserver pausing for 60 FPS efficiency and battery preservation.
 * - Full prefers-reduced-motion and Performance Mode support.
 */

import * as THREE from '../vendor/three.module.min.js';

export class HeroScene {
  constructor(containerId = 'hero-canvas-container', canvasId = 'hero-canvas') {
    this.container = document.getElementById(containerId);
    this.canvas = document.getElementById(canvasId);
    this.fallback = document.getElementById('hero-fallback-bg');

    this.isSupported = this.checkWebGLSupport();
    this.isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.isPerformanceMode = document.body.classList.contains('performance-mode');
    this.isVisible = true;

    this.animationFrameId = null;
    this.clock = new THREE.Clock();

    // Damped parallax targets
    this.targetRotationX = 0;
    this.targetRotationY = 0;
    this.currentRotationX = 0;
    this.currentRotationY = 0;

    if (this.isSupported && this.canvas) {
      this.init();
    } else {
      this.activateFallback('WebGL context unavailable');
    }
  }

  checkWebGLSupport() {
    try {
      const test = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && 
        (test.getContext('webgl') || test.getContext('experimental-webgl')));
    } catch (e) {
      return false;
    }
  }

  activateFallback(reason) {
    console.log(`[3D Hero] Using static gradient fallback: ${reason}`);
    if (this.canvas) this.canvas.style.display = 'none';
    if (this.fallback) this.fallback.style.display = 'block';
  }

  init() {
    try {
      const width = this.container.clientWidth || window.innerWidth;
      const height = this.container.clientHeight || window.innerHeight;

      // 1. Scene, Camera, and Fog for spatial atmospheric depth
      this.scene = new THREE.Scene();
      this.scene.fog = new THREE.FogExp2(0x010308, 0.08);

      this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
      this.camera.position.set(0, 1.1, 5.8);
      this.camera.lookAt(0, 0, 0);

      // 2. High-performance WebGL Renderer
      this.renderer = new THREE.WebGLRenderer({
        canvas: this.canvas,
        alpha: true,
        antialias: true,
        powerPreference: 'high-performance'
      });
      this.renderer.setSize(width, height);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

      // 3. Cinematic Spatial Lighting
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
      this.scene.add(ambientLight);

      const cyanKeyLight = new THREE.DirectionalLight(0x00f5d4, 2.6);
      cyanKeyLight.position.set(4, 5, 4);
      this.scene.add(cyanKeyLight);

      const violetFillLight = new THREE.DirectionalLight(0x9d4edd, 2.2);
      violetFillLight.position.set(-4, -3, 3);
      this.scene.add(violetFillLight);

      // 4. Scene Groups
      this.phoneGroup = new THREE.Group();
      this.scene.add(this.phoneGroup);

      this.createSmartphone();
      this.createHolographicRadarCone();
      this.createFloatingMarkers();
      this.createLidarPointCloud();
      this.createSonarPulseRings();

      // 5. Setup Observers & Listeners
      this.setupEventListeners();
      this.setupIntersectionObserver();

      // 6. Start Loop
      if (!this.isPerformanceMode) {
        this.start();
      } else {
        this.stop();
      }
    } catch (err) {
      console.warn('[3D Hero] Failed to initialize Three.js:', err);
      this.activateFallback('Error initializing 3D context');
    }
  }

  /**
   * Helper to create a dynamic Canvas texture representing a live HUD radar
   */
  createHudTexture() {
    this.hudCanvas = document.createElement('canvas');
    this.hudCanvas.width = 512;
    this.hudCanvas.height = 1024;
    this.hudCtx = this.hudCanvas.getContext('2d');
    this.hudTexture = new THREE.CanvasTexture(this.hudCanvas);
    return this.hudTexture;
  }

  updateHudCanvas(time) {
    if (!this.hudCtx) return;
    const ctx = this.hudCtx;
    const w = this.hudCanvas.width;
    const h = this.hudCanvas.height;

    // Clear dark screen
    ctx.fillStyle = '#03060f';
    ctx.fillRect(0, 0, w, h);

    // Subtle cyan grid lines
    ctx.strokeStyle = 'rgba(0, 245, 212, 0.12)';
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 40) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
    }
    for (let y = 0; y < h; y += 40) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    const cx = w / 2;
    const cy = h / 2 + 60;

    // Concentric Sonar range rings
    [100, 180, 260].forEach((r, idx) => {
      ctx.strokeStyle = 'rgba(0, 245, 212, 0.35)';
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 8]);
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
      
      // Distance labels
      ctx.fillStyle = 'rgba(112, 255, 240, 0.75)';
      ctx.font = 'bold 16px monospace';
      ctx.fillText(`${idx + 1}.0m`, cx + r - 25, cy - 8);
    });

    // Sweeping Radar beam line on phone screen
    const angle = (time * 2.5) % (Math.PI * 2);
    ctx.strokeStyle = '#00f5d4';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(angle) * 260, cy + Math.sin(angle) * 260);
    ctx.stroke();

    // Radar blip indicators
    // Blip 1: Person (Emerald)
    ctx.fillStyle = '#10b981';
    ctx.beginPath();
    ctx.arc(cx + 80, cy - 120, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillText('PERSON 1.8m', cx + 95, cy - 116);

    // Blip 2: Vehicle (Amber)
    ctx.fillStyle = '#f59e0b';
    ctx.beginPath();
    ctx.arc(cx - 110, cy - 90, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillText('VEHICLE 3.4m', cx - 210, cy - 86);

    // Blip 3: Stairs (Violet)
    ctx.fillStyle = '#d8b4fe';
    ctx.beginPath();
    ctx.arc(cx + 10, cy - 170, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillText('STAIRS 1.2m', cx + 25, cy - 166);

    // Top Status Header on phone screen
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 22px sans-serif';
    ctx.fillText('SPATIAL RADAR ACTIVE', 30, 60);

    ctx.fillStyle = '#00f5d4';
    ctx.font = '16px monospace';
    ctx.fillText('LATENCY: 0.02ms • 60 FPS', 30, 95);

    if (this.hudTexture) {
      this.hudTexture.needsUpdate = true;
    }
  }

  /**
   * Constructs the Glowing Smartphone model
   */
  createSmartphone() {
    // Phone Chassis
    const phoneGeo = new THREE.BoxGeometry(1.45, 2.9, 0.14);
    const phoneMat = new THREE.MeshStandardMaterial({
      color: 0x050812,
      metalness: 0.95,
      roughness: 0.2
    });
    const phoneMesh = new THREE.Mesh(phoneGeo, phoneMat);
    this.phoneGroup.add(phoneMesh);

    // Screen with dynamic live radar HUD texture
    const screenGeo = new THREE.PlaneGeometry(1.36, 2.78);
    const screenMat = new THREE.MeshBasicMaterial({
      map: this.createHudTexture()
    });
    const screenMesh = new THREE.Mesh(screenGeo, screenMat);
    screenMesh.position.z = 0.076;
    this.phoneGroup.add(screenMesh);

    // Screen glowing bevel edge
    const edgesGeo = new THREE.EdgesGeometry(phoneGeo);
    const edgesMat = new THREE.LineBasicMaterial({
      color: 0x00f5d4,
      transparent: true,
      opacity: 0.75
    });
    const edgesLine = new THREE.LineSegments(edgesGeo, edgesMat);
    this.phoneGroup.add(edgesLine);

    // Glowing Camera Lens Bump
    const lensGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.04, 24);
    lensGeo.rotateX(Math.PI / 2);
    const lensMat = new THREE.MeshStandardMaterial({
      color: 0x00f5d4,
      emissive: 0x00f5d4,
      emissiveIntensity: 2.2
    });
    this.cameraLens = new THREE.Mesh(lensGeo, lensMat);
    this.cameraLens.position.set(0, 1.22, 0.08);
    this.phoneGroup.add(this.cameraLens);
  }

  /**
   * Holographic Volumetric Radar Cone with Scanlines
   */
  createHolographicRadarCone() {
    this.radarGroup = new THREE.Group();
    this.radarGroup.position.set(0, 1.22, 0.1);

    const coneHeight = 3.8;
    const coneRadius = 1.75;
    const coneGeo = new THREE.ConeGeometry(coneRadius, coneHeight, 32, 2, true);
    coneGeo.rotateX(-Math.PI / 2);
    coneGeo.translate(0, 0, coneHeight / 2);

    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x00f5d4,
      transparent: true,
      opacity: 0.22,
      wireframe: true
    });
    this.radarCone = new THREE.Mesh(coneGeo, wireMat);
    this.radarGroup.add(this.radarCone);

    // Translucent violet inner scan veil
    const veilMat = new THREE.MeshBasicMaterial({
      color: 0x9d4edd,
      transparent: true,
      opacity: 0.08,
      side: THREE.DoubleSide
    });
    const veilMesh = new THREE.Mesh(coneGeo, veilMat);
    this.radarGroup.add(veilMesh);

    this.phoneGroup.add(this.radarGroup);
  }

  /**
   * 3D Floating Markers with Text Badges
   */
  createFloatingMarkers() {
    this.markers = [];

    const buildMarker = (colorHex, x, y, z, label, shapeType) => {
      const markerGroup = new THREE.Group();
      markerGroup.position.set(x, y, z);

      let geo;
      if (shapeType === 'person') {
        geo = new THREE.SphereGeometry(0.18, 16, 16);
      } else if (shapeType === 'car') {
        geo = new THREE.BoxGeometry(0.36, 0.24, 0.36);
      } else {
        geo = new THREE.OctahedronGeometry(0.24);
      }

      const mat = new THREE.MeshStandardMaterial({
        color: colorHex,
        emissive: colorHex,
        emissiveIntensity: 0.85,
        roughness: 0.2
      });
      const mesh = new THREE.Mesh(geo, mat);
      markerGroup.add(mesh);

      // Ground pulsing ring
      const ringGeo = new THREE.RingGeometry(0.32, 0.42, 32);
      ringGeo.rotateX(Math.PI / 2);
      const ringMat = new THREE.MeshBasicMaterial({
        color: colorHex,
        transparent: true,
        opacity: 0.6,
        side: THREE.DoubleSide
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.position.y = -0.35;
      markerGroup.add(ringMesh);

      // Point Light
      const pLight = new THREE.PointLight(colorHex, 1.8, 3.5);
      markerGroup.add(pLight);

      // Floating Text Label Sprite
      const spriteCanvas = document.createElement('canvas');
      spriteCanvas.width = 256;
      spriteCanvas.height = 64;
      const sCtx = spriteCanvas.getContext('2d');
      sCtx.fillStyle = 'rgba(3, 6, 15, 0.88)';
      sCtx.roundRect(4, 4, 248, 56, 14);
      sCtx.fill();
      sCtx.strokeStyle = '#' + colorHex.toString(16).padStart(6, '0');
      sCtx.lineWidth = 3;
      sCtx.stroke();
      sCtx.fillStyle = '#ffffff';
      sCtx.font = 'bold 24px monospace';
      sCtx.textAlign = 'center';
      sCtx.fillText(label, 128, 40);

      const spriteTexture = new THREE.CanvasTexture(spriteCanvas);
      const spriteMat = new THREE.SpriteMaterial({ map: spriteTexture, transparent: true });
      const sprite = new THREE.Sprite(spriteMat);
      sprite.scale.set(1.2, 0.3, 1);
      sprite.position.y = 0.38;
      markerGroup.add(sprite);

      this.scene.add(markerGroup);

      this.markers.push({
        group: markerGroup,
        ring: ringMesh,
        baseY: y,
        speed: 2 + Math.random()
      });
    };

    // Marker 1: Person (Emerald)
    buildMarker(0x10b981, 1.8, 0.3, 2.0, 'PERSON • 1.8M', 'person');

    // Marker 2: Car (Amber)
    buildMarker(0xf59e0b, -2.1, 0.1, 2.7, 'VEHICLE • 3.4M', 'car');

    // Marker 3: Stairs (Violet)
    buildMarker(0x9d4edd, 0.3, -0.7, 1.8, 'STAIRS • 1.2M', 'stairs');
  }

  /**
   * Drifting 3D LiDAR point cloud particles representing spatial depth
   */
  createLidarPointCloud() {
    const particleCount = 180;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const cyanColor = new THREE.Color(0x00f5d4);
    const violetColor = new THREE.Color(0x9d4edd);

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 6;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 3 + 0.5;
      positions[i * 3 + 2] = Math.random() * 4 + 0.5;

      const mixed = Math.random() > 0.5 ? cyanColor : violetColor;
      colors[i * 3] = mixed.r;
      colors[i * 3 + 1] = mixed.g;
      colors[i * 3 + 2] = mixed.b;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 0.05,
      vertexColors: true,
      transparent: true,
      opacity: 0.55
    });

    this.pointCloud = new THREE.Points(geometry, material);
    this.scene.add(this.pointCloud);
  }

  createSonarPulseRings() {
    this.sonarRings = [];
    for (let i = 0; i < 3; i++) {
      const ringGeo = new THREE.RingGeometry(0.3, 0.4, 32);
      ringGeo.rotateX(Math.PI / 2);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0x00f5d4,
        transparent: true,
        opacity: 0.45,
        side: THREE.DoubleSide
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.position.set(0, 1.22, 0.1);
      this.phoneGroup.add(ring);
      this.sonarRings.push({
        mesh: ring,
        offset: i / 3
      });
    }
  }

  setupEventListeners() {
    window.addEventListener('pointermove', (e) => {
      const normX = (e.clientX / window.innerWidth) * 2 - 1;
      const normY = -(e.clientY / window.innerHeight) * 2 + 1;
      this.targetRotationY = normX * 0.45;
      this.targetRotationX = normY * 0.25;
    }, { passive: true });

    window.addEventListener('deviceorientation', (e) => {
      if (e.gamma !== null && e.beta !== null) {
        this.targetRotationY = (e.gamma / 45) * 0.45;
        this.targetRotationX = ((e.beta - 45) / 45) * 0.25;
      }
    }, { passive: true });

    window.addEventListener('resize', () => {
      if (!this.container || !this.renderer || !this.camera) return;
      const width = this.container.clientWidth || window.innerWidth;
      const height = this.container.clientHeight || window.innerHeight;
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(width, height);
    });

    window.addEventListener('performance-mode-changed', (e) => {
      this.isPerformanceMode = e.detail.enabled;
      if (this.isPerformanceMode) {
        this.stop();
        if (this.canvas) this.canvas.style.display = 'none';
        if (this.fallback) this.fallback.style.display = 'block';
      } else {
        if (this.canvas) this.canvas.style.display = 'block';
        if (this.fallback) this.fallback.style.display = 'none';
        this.start();
      }
    });

    window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
      this.isReducedMotion = e.matches;
    });
  }

  setupIntersectionObserver() {
    if ('IntersectionObserver' in window && this.container) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          this.isVisible = entry.isIntersecting;
          if (this.isVisible && !this.isPerformanceMode) {
            this.start();
          } else {
            this.stop();
          }
        });
      }, { threshold: 0.1 });

      observer.observe(this.container);
    }
  }

  start() {
    if (this.animationFrameId) return;
    this.clock.start();
    this.render();
  }

  stop() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  render = () => {
    this.animationFrameId = requestAnimationFrame(this.render);

    const delta = this.clock.getDelta();
    const time = this.clock.getElapsedTime();

    // Damped Lerp Parallax
    this.currentRotationX += (this.targetRotationX - this.currentRotationX) * 0.05;
    this.currentRotationY += (this.targetRotationY - this.currentRotationY) * 0.05;

    this.camera.position.x = this.currentRotationY * 1.6;
    this.camera.position.y = 1.1 + this.currentRotationX * 0.8;
    this.camera.lookAt(0, 0.3, 0);

    // Update Live HUD Canvas Texture
    this.updateHudCanvas(time);

    if (!this.isReducedMotion) {
      this.phoneGroup.rotation.y = Math.sin(time * 0.7) * 0.32;
      this.phoneGroup.rotation.x = Math.sin(time * 0.5) * 0.08;
      this.phoneGroup.position.y = Math.sin(time * 1.2) * 0.04;

      if (this.radarGroup) {
        this.radarGroup.rotation.y = Math.sin(time * 2.2) * 0.55;
      }

      this.markers.forEach((m, idx) => {
        m.group.position.y = m.baseY + Math.sin(time * m.speed + idx) * 0.08;
        const ringScale = 1 + Math.sin(time * 3 + idx) * 0.2;
        m.ring.scale.set(ringScale, ringScale, ringScale);
      });

      this.sonarRings.forEach((item) => {
        const progress = (time * 0.65 + item.offset) % 1;
        const scale = 1 + progress * 4.2;
        item.mesh.scale.set(scale, scale, scale);
        item.mesh.material.opacity = (1 - progress) * 0.5;
      });

      if (this.pointCloud) {
        this.pointCloud.rotation.y = time * 0.03;
      }
    } else {
      this.phoneGroup.rotation.set(0.04, 0.12, 0);
      if (this.radarGroup) this.radarGroup.rotation.set(0, 0, 0);
    }

    this.renderer.render(this.scene, this.camera);
  };
}
