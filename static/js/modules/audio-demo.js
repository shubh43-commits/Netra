/**
 * Blind Assist Navigator - Sensory Audio & Haptics Simulator Module
 * 
 * Provides an interactive in-browser preview of the spatial acoustics and tactile cues.
 * Uses Web Audio API (StereoPannerNode / OscillatorNode) and browser Vibration API.
 */

export class AudioDemoManager {
  constructor() {
    this.audioCtx = null;
    this.init();
  }

  init() {
    // Wire up buttons for Left, Center, Right spatial acoustic test
    const leftBtn = document.getElementById('test-audio-left');
    const centerBtn = document.getElementById('test-audio-center');
    const rightBtn = document.getElementById('test-audio-right');
    const vibrateBtn = document.getElementById('test-vibration-btn');
    const visualizer = document.getElementById('soundwave-visualizer');

    if (leftBtn) {
      leftBtn.addEventListener('click', () => this.playSpatialBeep(-0.85, 440, 'Obstacle detected 2 meters on your left'));
    }
    if (centerBtn) {
      centerBtn.addEventListener('click', () => this.playSpatialBeep(0.0, 600, 'Obstacle detected 1.5 meters directly ahead'));
    }
    if (rightBtn) {
      rightBtn.addEventListener('click', () => this.playSpatialBeep(0.85, 880, 'Obstacle detected 3 meters on your right'));
    }
    if (vibrateBtn) {
      vibrateBtn.addEventListener('click', () => this.triggerHapticPattern());
    }
  }

  /**
   * Lazily initializes AudioContext on user gesture
   */
  getAudioContext() {
    if (!this.audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        this.audioCtx = new AudioContextClass();
      }
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
    return this.audioCtx;
  }

  /**
   * Plays a true binaural directional audio beep
   * @param {number} panValue - -1.0 (hard left) to +1.0 (hard right)
   * @param {number} frequency - Hz pitch (higher pitch for closer or critical obstacles)
   * @param {string} spokenMsg - Optional announcement for screen readers
   */
  playSpatialBeep(panValue, frequency, spokenMsg) {
    const ctx = this.getAudioContext();
    if (!ctx) return;

    // Visual feedback
    this.animateVisualizer();

    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(frequency, now);

    // Fade in and out smoothly (avoid clicks)
    gain.gain.setValueAtTime(0.001, now);
    gain.gain.exponentialRampToValueAtTime(0.35, now + 0.03);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);

    // Spatial Panning (Binaural stereo placement)
    if (ctx.createStereoPanner) {
      const panner = ctx.createStereoPanner();
      panner.pan.setValueAtTime(panValue, now);
      osc.connect(gain);
      gain.connect(panner);
      panner.connect(ctx.destination);
    } else {
      osc.connect(gain);
      gain.connect(ctx.destination);
    }

    osc.start(now);
    osc.stop(now + 0.3);

    // Announce to Screen Readers
    if (spokenMsg) {
      const announcer = document.getElementById('aria-announcer');
      if (announcer) {
        announcer.textContent = spokenMsg;
      }
    }
  }

  /**
   * Triggers tactile cadence using Vibration API
   */
  triggerHapticPattern() {
    if ('vibrate' in navigator) {
      // 120ms pulse, 80ms pause, 200ms pulse (urgent obstacle warning pattern)
      navigator.vibrate([120, 80, 200]);
      const announcer = document.getElementById('aria-announcer');
      if (announcer) {
        announcer.textContent = 'Haptic vibration pulse triggered.';
      }
    } else {
      const announcer = document.getElementById('aria-announcer');
      if (announcer) {
        announcer.textContent = 'Vibration API is not supported on this device/browser.';
      }
    }
  }

  animateVisualizer() {
    const bars = document.querySelectorAll('.soundwave-bar');
    bars.forEach((bar, i) => {
      bar.classList.add('active');
      setTimeout(() => {
        bar.classList.remove('active');
      }, 400 + i * 50);
    });
  }
}
