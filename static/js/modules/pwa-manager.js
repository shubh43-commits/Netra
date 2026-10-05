/**
 * Blind Assist Navigator - PWA Manager Module
 * Handles Service Worker lifecycle, installation prompts, and online/offline connectivity alerts.
 */

export class PWAManager {
  constructor() {
    this.deferredPrompt = null;
    this.installBtn = document.getElementById('pwa-install-btn');
    this.networkStatusEl = document.getElementById('network-status');
    this.ariaAnnouncer = document.getElementById('aria-announcer');

    this.init();
  }

  init() {
    this.registerServiceWorker();
    this.setupInstallPrompt();
    this.setupConnectivityListeners();
  }

  /**
   * Registers the Service Worker served from the root scope /sw.js
   */
  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
        console.log('[PWA] Service Worker registered successfully with scope:', registration.scope);

        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                this.announce(_('App updated. Refresh to access the latest version.'));
              }
            });
          }
        });
      } catch (error) {
        console.warn('[PWA] Service Worker registration failed:', error);
      }
    }
  }

  /**
   * Captures the beforeinstallprompt event to enable one-click accessible installation
   */
  setupInstallPrompt() {
    window.addEventListener('beforeinstallprompt', (e) => {
      // Prevent automatic browser mini-infobar
      e.preventDefault();
      this.deferredPrompt = e;

      // Reveal install button if present in UI
      if (this.installBtn) {
        this.installBtn.hidden = false;
        this.installBtn.setAttribute('aria-hidden', 'false');
        this.installBtn.addEventListener('click', () => this.promptInstall());
      }
    });

    window.addEventListener('appinstalled', () => {
      console.log('[PWA] Blind Assist Navigator successfully installed');
      this.deferredPrompt = null;
      if (this.installBtn) {
        this.installBtn.hidden = true;
      }
      this.announce('Blind Assist Navigator installed to your home screen.');
    });
  }

  async promptInstall() {
    if (!this.deferredPrompt) return;

    this.deferredPrompt.prompt();
    const { outcome } = await this.deferredPrompt.userChoice;
    console.log(`[PWA] Install prompt outcome: ${outcome}`);
    this.deferredPrompt = null;
  }

  /**
   * Listens for network status changes to inform screen-reader users
   */
  setupConnectivityListeners() {
    window.addEventListener('online', () => {
      this.announce('Internet connection restored. Live features reconnected.');
      if (this.networkStatusEl) {
        this.networkStatusEl.textContent = 'Online';
        this.networkStatusEl.className = 'badge badge-emerald';
      }
    });

    window.addEventListener('offline', () => {
      this.announce('Internet disconnected. Operating in offline on-device mode.');
      if (this.networkStatusEl) {
        this.networkStatusEl.textContent = 'Offline (On-Device)';
        this.networkStatusEl.className = 'badge badge-amber';
      }
    });
  }

  /**
   * Speaks or announces text to assistive technologies via aria-live
   */
  announce(message) {
    if (this.ariaAnnouncer) {
      this.ariaAnnouncer.textContent = message;
    }
  }
}
