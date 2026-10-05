/**
 * Blind Assist Navigator - Performance Mode Module
 * Allows users on battery saving, older phones, or with motion sensitivities to disable heavy
 * WebGL renders and CSS blur filters. Persists setting in localStorage.
 */

export class PerformanceModeManager {
  constructor() {
    this.storageKey = 'blind-assist-perf-mode';
    this.toggleBtn = document.getElementById('perf-toggle-btn');
    this.ariaAnnouncer = document.getElementById('aria-announcer');
    this.isEnabled = false;

    this.init();
  }

  init() {
    // Check saved state or system preference for reduced motion / battery
    const saved = localStorage.getItem(this.storageKey);
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (saved !== null) {
      this.isEnabled = saved === 'true';
    } else if (prefersReducedMotion) {
      this.isEnabled = true;
    }

    this.applyState(this.isEnabled, false);

    if (this.toggleBtn) {
      this.toggleBtn.addEventListener('click', () => this.toggle());
      this.toggleBtn.addEventListener('keydown', (e) => {
        if (e.key === ' ' || e.key === 'Enter') {
          e.preventDefault();
          this.toggle();
        }
      });
    }
  }

  toggle() {
    this.applyState(!this.isEnabled, true);
  }

  applyState(enable, announceChange = true) {
    this.isEnabled = enable;
    localStorage.setItem(this.storageKey, this.isEnabled ? 'true' : 'false');

    if (this.isEnabled) {
      document.body.classList.add('performance-mode');
    } else {
      document.body.classList.remove('performance-mode');
    }

    if (this.toggleBtn) {
      this.toggleBtn.setAttribute('aria-checked', this.isEnabled ? 'true' : 'false');
      const label = this.toggleBtn.querySelector('.toggle-label');
      if (label) {
        label.textContent = this.isEnabled ? 'Performance: High (2D)' : 'Performance: Standard (3D)';
      }
    }

    // Broadcast custom event so Three.js hero scene knows to pause/resume
    window.dispatchEvent(new CustomEvent('performance-mode-changed', {
      detail: { enabled: this.isEnabled }
    }));

    if (announceChange && this.ariaAnnouncer) {
      this.ariaAnnouncer.textContent = this.isEnabled
        ? 'Performance mode enabled. 3D effects and animations disabled for battery savings.'
        : 'Performance mode disabled. Full 3D visual effects enabled.';
    }
  }

  isActive() {
    return this.isEnabled;
  }
}
