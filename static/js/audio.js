/**
 * Netra Audio & Haptic Feedback Engine
 * Handles:
 * - Directional spatial stereo beeps via Web Audio API (StereoPannerNode + Oscillator)
 * - Proximity pitch & pulse rate modulation (closer = higher pitch & faster beeps)
 * - Natural speech announcements via Web Speech API (en-IN & hi-IN support)
 * - Haptic vibration patterns via navigator.vibrate
 * - Auto-unlock on user gesture (audio context resume)
 */

class NetraAudioEngine {
  constructor() {
    this.audioCtx = null;
    this.panner = null;
    this.masterGain = null;
    this.unlocked = false;
    this.muted = false;
    this.language = localStorage.getItem('netra_lang') || 'en';
    this.speechRate = parseFloat(localStorage.getItem('netra_speech_rate') || '1.0');
    this.volume = parseFloat(localStorage.getItem('netra_volume') || '0.8');
    this.vibrationEnabled = localStorage.getItem('netra_vibration') !== 'false';
    this.spatialBeepsEnabled = localStorage.getItem('netra_beeps') !== 'false';
    this.speechEnabled = localStorage.getItem('netra_speech') !== 'false';

    this.lastSpokenText = '';
    this.lastSpokenTime = 0;
    this.activeBeepTimer = null;
    this.speechQueue = [];
    this.isSpeaking = false;

    // Preload available speech voices
    this.voices = [];
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = () => {
        this.voices = window.speechSynthesis.getVoices();
      };
      this.voices = window.speechSynthesis.getVoices();
    }
  }

  /**
   * Unlock AudioContext on first user interaction (browser policy)
   */
  unlock() {
    if (this.unlocked && this.audioCtx && this.audioCtx.state === 'running') return;

    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return;

      if (!this.audioCtx) {
        this.audioCtx = new AudioContextClass();
      }

      if (this.audioCtx.state === 'suspended') {
        this.audioCtx.resume();
      }

      // Master gain
      this.masterGain = this.audioCtx.createGain();
      this.masterGain.gain.setValueAtTime(this.volume, this.audioCtx.currentTime);

      // Stereo panner
      if (typeof this.audioCtx.createStereoPanner === 'function') {
        this.panner = this.audioCtx.createStereoPanner();
        this.panner.connect(this.masterGain);
      } else {
        // Fallback for older Safari
        this.panner = null;
      }

      this.masterGain.connect(this.audioCtx.destination);
      this.unlocked = true;
    } catch (e) {
      console.warn('[Netra Audio] Could not initialize Web Audio context:', e);
    }
  }

  /**
   * Play a directional proximity beep.
   * @param {string} direction - 'left', 'ahead', 'right'
   * @param {number} distanceM - Distance in meters (e.g. 1.5, 4.0)
   * @param {number} durationSec - Beep duration in seconds (default: 0.12)
   */
  playProximityBeep(direction = 'ahead', distanceM = 3.0, durationSec = 0.12) {
    if (this.muted || !this.spatialBeepsEnabled) return;
    this.unlock();
    if (!this.audioCtx) return;

    try {
      const now = this.audioCtx.currentTime;
      const osc = this.audioCtx.createOscillator();
      const noteGain = this.audioCtx.createGain();

      // Pitch calculation: closer = higher frequency (320 Hz at 8m up to 920 Hz at 0.5m)
      const clampedDist = Math.max(0.4, Math.min(8.0, distanceM));
      const freq = 920 - ((clampedDist - 0.4) / (8.0 - 0.4)) * 600;
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, now);

      // Stereo pan: left = -0.9, ahead = 0.0, right = +0.9
      let panVal = 0.0;
      if (direction === 'left') panVal = -0.9;
      else if (direction === 'right') panVal = 0.9;

      if (this.panner && this.panner.pan) {
        this.panner.pan.setValueAtTime(panVal, now);
        noteGain.connect(this.panner);
      } else {
        noteGain.connect(this.masterGain);
      }

      // Envelope: smooth attack & decay to prevent clicking
      noteGain.gain.setValueAtTime(0.001, now);
      noteGain.gain.exponentialRampToValueAtTime(0.6 * this.volume, now + 0.02);
      noteGain.gain.exponentialRampToValueAtTime(0.001, now + durationSec);

      osc.connect(noteGain);
      osc.start(now);
      osc.stop(now + durationSec + 0.05);
    } catch (e) {
      console.warn('[Netra Audio] Error playing beep:', e);
    }
  }

  /**
   * Speak a spoken warning aloud with rate and queue throttling.
   * @param {string} text - Message to speak
   * @param {boolean} urgent - If true, cancels ongoing speech to announce immediately
   */
  speak(text, urgent = false) {
    if (this.muted || !this.speechEnabled || !text) return;
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;

    const now = Date.now();
    // Prevent repeating identical sentence within 3 seconds unless urgent
    if (!urgent && text === this.lastSpokenText && (now - this.lastSpokenTime) < 3000) {
      return;
    }

    if (urgent) {
      window.speechSynthesis.cancel();
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = this.speechRate;
    utterance.volume = this.volume;

    // Select voice according to language
    const langCode = this.language === 'hi' ? 'hi-IN' : 'en-IN';
    utterance.lang = langCode;

    if (this.voices.length > 0) {
      const match = this.voices.find(v => v.lang.startsWith(this.language) || v.lang.includes(langCode));
      if (match) utterance.voice = match;
    }

    utterance.onend = () => {
      this.isSpeaking = false;
    };
    utterance.onerror = () => {
      this.isSpeaking = false;
    };

    this.lastSpokenText = text;
    this.lastSpokenTime = now;
    this.isSpeaking = true;
    window.speechSynthesis.speak(utterance);
  }

  /**
   * Trigger haptic vibration pattern based on severity
   * @param {string} severity - 'warning', 'critical', 'tap'
   */
  vibrate(severity = 'warning') {
    if (!this.vibrationEnabled || typeof navigator === 'undefined' || !('vibrate' in navigator)) {
      return;
    }

    try {
      if (severity === 'critical') {
        navigator.vibrate([250, 80, 250, 80, 350]);
      } else if (severity === 'warning') {
        navigator.vibrate([150, 60, 150]);
      } else {
        navigator.vibrate(60);
      }
    } catch (e) {
      // Vibration not permitted or supported
    }
  }

  /**
   * Alert user for an identified hazard (combination of sound, speech and haptics)
   */
  alertHazard(item, spokenText = null) {
    if (!item) return;

    const dist = item.distance_m || 3.0;
    const dir = item.direction || 'ahead';
    const approaching = Boolean(item.approaching);

    // Beep immediately
    this.playProximityBeep(dir, dist, approaching ? 0.18 : 0.12);

    // Vibrate
    if (dist < 2.0 || approaching) {
      this.vibrate('critical');
    } else {
      this.vibrate('warning');
    }

    // Speak
    if (spokenText) {
      this.speak(spokenText, dist < 1.8);
    }
  }

  setMuted(muted) {
    this.muted = muted;
    if (muted && typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }

  setLanguage(lang) {
    this.language = lang;
    localStorage.setItem('netra_lang', lang);
  }
}

// Global Netra audio singleton
window.netraAudio = new NetraAudioEngine();
