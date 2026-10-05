/**
 * Netra Radar Component
 * Renders an accessible 2D top-down spatial mini-map radar
 * - Violet concentric distance rings (1m, 3m, 6m)
 * - Directional sectors: Left, Ahead, Right
 * - Center point representing user
 * - Detected objects plotted dynamically with hazard pulsing
 */

class NetraRadar {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.items = [];
    this.maxDistance = 8.0; // 8 meters maximum range
    this.initCanvas();
    window.addEventListener('resize', () => this.initCanvas());
  }

  initCanvas() {
    if (!this.canvas) return;
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.width = rect.width || 280;
    this.height = rect.height || 280;
    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.ctx.scale(dpr, dpr);
    this.render();
  }

  update(items = []) {
    this.items = items;
    this.render();
  }

  render() {
    if (!this.ctx) return;
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    const cx = w / 2;
    const cy = h * 0.85; // User positioned near bottom center
    const maxRadius = h * 0.75;

    ctx.clearRect(0, 0, w, h);

    // 1. Directional sector lines
    ctx.strokeStyle = 'rgba(21, 18, 31, 0.12)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);

    // -30 deg, +30 deg field of view lines
    const fovAngle = Math.PI / 6; // 30 degrees
    [-fovAngle, fovAngle].forEach((ang) => {
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + Math.sin(ang) * maxRadius, cy - Math.cos(ang) * maxRadius);
      ctx.stroke();
    });

    ctx.setLineDash([]);

    // 2. Distance circles (2m, 4m, 6m, 8m)
    const rings = [2.0, 4.0, 6.0, 8.0];
    rings.forEach((dist) => {
      const r = (dist / this.maxDistance) * maxRadius;
      ctx.beginPath();
      ctx.arc(cx, cy, r, Math.PI, 0); // Upper half circle
      ctx.strokeStyle = dist === 2.0 ? 'rgba(91, 61, 245, 0.45)' : 'rgba(91, 61, 245, 0.2)';
      ctx.lineWidth = dist === 2.0 ? 2 : 1;
      ctx.stroke();

      // Distance label
      ctx.fillStyle = '#5f5a6e';
      ctx.font = '10px "Atkinson Hyperlegible", sans-serif';
      ctx.fillText(`${dist}m`, cx + 6, cy - r + 11);
    });

    // 3. Center user marker
    ctx.beginPath();
    ctx.arc(cx, cy, 7, 0, Math.PI * 2);
    ctx.fillStyle = '#15121f';
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cx, cy, 12, 0, Math.PI * 2);
    ctx.strokeStyle = '#5b3df5';
    ctx.lineWidth = 2;
    ctx.stroke();

    // 4. Render detected items
    this.items.forEach((item) => {
      const dist = Math.min(this.maxDistance, Math.max(0.5, item.distance_m || 3.0));
      const r = (dist / this.maxDistance) * maxRadius;

      // Determine angle from direction
      let angle = 0;
      if (item.direction === 'left') angle = -0.38;
      else if (item.direction === 'right') angle = 0.38;
      else angle = 0; // ahead

      // If item has normalized box coordinates, refine angle
      if (item.box && item.box.length === 4) {
        const boxCx = item.box[0] + item.box[2] / 2;
        angle = (boxCx - 0.5) * (Math.PI / 2.5); // spread across fov
      }

      const x = cx + Math.sin(angle) * r;
      const y = cy - Math.cos(angle) * r;

      // Item color based on danger class
      let dotColor = '#5b3df5';
      if (item.class_name === 'car' || item.class_name === 'stairs') dotColor = '#ff7ab6';
      else if (item.class_name === 'person') dotColor = '#3db8ff';
      else dotColor = '#d4f55a';

      // Outer hazard pulse ring if approaching or close
      if (item.approaching || dist <= 2.0) {
        ctx.beginPath();
        ctx.arc(x, y, 14, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 122, 182, 0.35)';
        ctx.fill();
      }

      // Main dot
      ctx.beginPath();
      ctx.arc(x, y, 8, 0, Math.PI * 2);
      ctx.fillStyle = dotColor;
      ctx.fill();
      ctx.strokeStyle = '#15121f';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Label
      ctx.fillStyle = '#15121f';
      ctx.font = 'bold 11px "Atkinson Hyperlegible", sans-serif';
      const label = `${item.class_name || 'obstacle'} (${dist.toFixed(1)}m)`;
      ctx.fillText(label, x + 10, y + 4);
    });
  }
}

window.NetraRadar = NetraRadar;
