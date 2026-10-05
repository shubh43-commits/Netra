/**
 * Netra - 3D Echolocation Hero Scene
 * Powered by Three.js (r128)
 *
 * Visualizes echolocation waves rolling outward across the walking plane.
 * As violet sound waves reach hazard markers (obstacles), the markers pulse/pop.
 * Responds gently to pointer movement and device gyroscope orientation.
 * Fully accessible: Respects prefers-reduced-motion, includes Calm Mode toggle,
 * and falls back gracefully if WebGL is unavailable.
 */

(function initHero3D() {
  const canvas = document.getElementById("gl");
  const calmBtn = document.getElementById("perf");
  if (!canvas || typeof THREE === "undefined") {
    if (canvas) canvas.style.display = "none";
    if (calmBtn) calmBtn.style.display = "none";
    return;
  }

  const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let calm = false;
  let renderer = null;
  let ok = true;

  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  } catch (e) {
    ok = false;
    canvas.style.display = "none";
    if (calmBtn) calmBtn.style.display = "none";
    return;
  }

  if (!ok) return;

  const VIO = 0x5b3df5;
  const INK = 0x15121f;
  const R = 8;
  const NR = 5;

  const scene = new THREE.Scene();
  const cam = new THREE.PerspectiveCamera(40, 1, 0.1, 80);
  cam.position.set(0, 3.6, 9.5);
  cam.lookAt(0, 0, -0.5);

  const world = new THREE.Group();
  scene.add(world);

  // Center emitter core and pulsating halo
  const core = new THREE.Mesh(
    new THREE.SphereGeometry(0.16, 32, 32),
    new THREE.MeshBasicMaterial({ color: INK })
  );
  core.position.y = 0.16;
  world.add(core);

  const halo = new THREE.Mesh(
    new THREE.RingGeometry(0.3, 0.34, 64),
    new THREE.MeshBasicMaterial({ color: VIO, transparent: true, opacity: 0.8, side: THREE.DoubleSide })
  );
  halo.rotation.x = -Math.PI / 2;
  world.add(halo);

  // Expanding sound wave rings
  const rings = [];
  for (let i = 0; i < NR; i++) {
    const m = new THREE.Mesh(
      new THREE.RingGeometry(0.985, 1, 160),
      new THREE.MeshBasicMaterial({ color: VIO, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false })
    );
    m.rotation.x = -Math.PI / 2;
    world.add(m);
    rings.push(m);
  }

  // Static guideline rings on the floor
  [2.5, 5, 7.5].forEach((radius) => {
    const g = new THREE.Mesh(
      new THREE.RingGeometry(radius - 0.01, radius + 0.01, 160),
      new THREE.MeshBasicMaterial({ color: INK, transparent: true, opacity: 0.1, side: THREE.DoubleSide })
    );
    g.rotation.x = -Math.PI / 2;
    world.add(g);
  });

  // Hazard markers (coloured spheres on ink pillars with ink outline)
  const COL = [0xff7ab6, 0xc6f03a, 0x5b3df5, 0xff9a3c, 0x3db8ff, 0xff7ab6, 0xc6f03a, 0x5b3df5];
  const spots = [
    [2.4, -1.1, 1.1],
    [4.1, 0.5, 0.8],
    [3.3, 1.8, 1.5],
    [5.6, -0.4, 0.9],
    [6.4, 1.2, 0.7],
    [1.6, 2.4, 0.8],
    [5, -2, 1.2],
    [3, -2.4, 0.7]
  ];

  const hz = spots.map(([d, a, h], i) => {
    const g = new THREE.Group();
    g.position.set(Math.sin(a) * d * 0.9, 0, -Math.cos(a) * d);

    // Ink pillar
    const line = new THREE.Mesh(
      new THREE.CylinderGeometry(0.018, 0.018, h, 8),
      new THREE.MeshBasicMaterial({ color: INK })
    );
    line.position.y = h / 2;
    g.add(line);

    // Coloured hazard sphere
    const tip = new THREE.Mesh(
      new THREE.SphereGeometry(0.14, 24, 24),
      new THREE.MeshBasicMaterial({ color: COL[i % COL.length] })
    );
    tip.position.y = h;
    g.add(tip);

    // Ink outline sphere (back-side rendered for crisp outline)
    const outline = new THREE.Mesh(
      new THREE.SphereGeometry(0.17, 24, 24),
      new THREE.MeshBasicMaterial({ color: INK, side: THREE.BackSide })
    );
    outline.position.y = h;
    g.add(outline);

    world.add(g);
    return {
      g,
      tip,
      outline,
      dist: Math.hypot(g.position.x, g.position.z),
      h
    };
  });

  // Tilt & Pointer Interaction
  let tx = 0, ty = 0, cx = 0, cy = 0;
  window.addEventListener("pointermove", (e) => {
    tx = e.clientX / window.innerWidth - 0.5;
    ty = e.clientY / window.innerHeight - 0.5;
  }, { passive: true });

  window.addEventListener("deviceorientation", (e) => {
    if (e.gamma != null) {
      tx = Math.max(-0.5, Math.min(0.5, e.gamma / 60));
      ty = Math.max(-0.5, Math.min(0.5, (e.beta - 50) / 80));
    }
  }, { passive: true });

  function resize() {
    const heroEl = document.querySelector(".hero");
    const w = window.innerWidth;
    const h = heroEl ? heroEl.offsetHeight : window.innerHeight;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, calm ? 1 : 2));
    renderer.setSize(w, h, false);
    cam.aspect = w / h;
    const wide = w / h > 1.1;
    world.position.set(wide ? 3.4 : 0, wide ? 0 : -1.8, wide ? 0 : -2);
    world.scale.setScalar(wide ? 1 : 0.72);
    cam.updateProjectionMatrix();
  }

  window.addEventListener("resize", resize);
  resize();

  const clock = new THREE.Clock();

  function frame() {
    const t = clock.getElapsedTime();
    cx += (tx - cx) * 0.04;
    cy += (ty - cy) * 0.04;

    world.rotation.y = cx * 0.4;
    cam.position.y = 3.6 + cy * 0.9;
    cam.lookAt(0, 0, -0.5);

    const radii = [];
    rings.forEach((m, i) => {
      const k = (t * 0.16 + i / NR) % 1;
      const r = Math.max(0.01, k * R);
      radii.push(r);
      m.scale.set(r, r, 1);
      m.material.opacity = Math.pow(1 - k, 1.4) * 0.6;
    });

    halo.material.opacity = 0.5 + Math.sin(t * 3) * 0.3;

    hz.forEach((h) => {
      let b = 0;
      radii.forEach((r) => {
        b = Math.max(b, Math.exp(-Math.pow(r - h.dist, 2) / 0.08));
      });
      const s = 1 + b * 0.7;
      h.tip.scale.set(s, s, s);
      h.outline.scale.set(s, s, s);
      h.tip.position.y = h.outline.position.y = h.h + b * 0.25;
    });

    renderer.render(scene, cam);

    if (!still && !calm) {
      requestAnimationFrame(frame);
    }
  }

  frame();

  if (calmBtn) {
    calmBtn.addEventListener("click", function () {
      calm = !calm;
      this.setAttribute("aria-pressed", calm ? "true" : "false");
      this.textContent = calm ? (this.dataset.calmOn || "Calm: on") : (this.dataset.calmMode || "Calm mode");
      resize();
      if (!calm && !still) {
        frame();
      }
    });
  }
})();
