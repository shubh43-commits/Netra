/**
 * Netra - Home Page Interactive Scripts
 * Handles:
 * - Rotating live alert speech-bubble preview with smooth fade
 * - Accessible IntersectionObserver scroll reveals for .rv elements
 */

document.addEventListener('DOMContentLoaded', () => {
  // Alert preview text cycling
  const alertEl = document.getElementById('alert');
  if (alertEl) {
    let alertLines = [
      "All clear ahead.",
      "Person, ahead, 4 metres.",
      "Car coming, left, 6 metres.",
      "Stairs, right, 2 metres.",
      "Green light. You can cross."
    ];

    // Read localized lines if provided in template
    const localizedData = document.getElementById('alert-lines-data');
    if (localizedData) {
      try {
        const parsed = JSON.parse(localizedData.textContent);
        if (Array.isArray(parsed) && parsed.length > 0) {
          alertLines = parsed;
        }
      } catch (e) {
        console.warn('Failed to parse localized alert lines:', e);
      }
    }

    let lineIndex = 0;
    setInterval(() => {
      alertEl.style.opacity = '0';
      setTimeout(() => {
        lineIndex = (lineIndex + 1) % alertLines.length;
        alertEl.textContent = alertLines[lineIndex];
        alertEl.style.opacity = '1';
      }, 400);
    }, 3000);

    // Interactive audio preview on click
    const heroBubble = document.getElementById('heroBubble');
    if (heroBubble) {
      const playBubbleAudio = () => {
        if (window.netraAudio) {
          window.netraAudio.unlock();
          const currentText = alertEl ? alertEl.textContent : alertLines[lineIndex];
          let dir = 'ahead';
          if (currentText.toLowerCase().includes('left')) dir = 'left';
          else if (currentText.toLowerCase().includes('right')) dir = 'right';
          window.netraAudio.playProximityBeep(dir, 2.5);
          window.netraAudio.speak(currentText, true);
        }
      };

      heroBubble.addEventListener('click', playBubbleAudio);
      heroBubble.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          playBubbleAudio();
        }
      });
    }
  }

  // Scroll reveal with staggered entrance animation
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!prefersReducedMotion && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });

    document.querySelectorAll('.rv').forEach((el, index) => {
      el.style.transitionDelay = (index % 3) * 90 + 'ms';
      observer.observe(el);
    });
  } else {
    // If reduced motion is preferred or IntersectionObserver is unsupported, reveal all immediately
    document.querySelectorAll('.rv').forEach((el) => {
      el.classList.add('in');
    });
  }
});
