# Netra AI & Assistive Navigation - System Documentation

Welcome to the internal engineering and architectural documentation for **Netra**.

---

## Directory & File Structure

```text
NetraAI/
├── apps/                          # Modular Django Domain Applications
│   ├── accounts/                  # Authentication, UserProfile, Device sync, EmergencyContacts
│   ├── analytics/                 # Privacy-first telemetry aggregation, safety incidents
│   ├── core/                      # Core health endpoints, PWA manifests, base utilities
│   ├── detection/                 # Real-time YOLO inference, IoU tracking, WebSocket streaming
│   ├── feedback/                  # Human-in-the-loop report collector, active model feedback
│   └── modelhub/                  # Model version management, weights hot-reloading
├── config/                        # ASGI / WSGI server configuration and environment settings
│   ├── asgi.py                    # Daphne ASGI entrypoint with WebSocket routing
│   ├── urls.py                    # Root URL dispatching (API, Auth, Profile, Admin, PWA)
│   ├── wsgi.py                    # WSGI fallback entrypoint
│   └── settings/                  # Environment-specific settings (base, dev, prod)
├── docs/                          # Architectural documentation, deployment & mobile guides
│   ├── README.md                  # Documentation index (this file)
│   └── MOBILE_RESPONSIVE_SYSTEM.md# Mobile phone UX standards, tactile guidelines, PWA
├── locale/                        # Internationalization translations (English 'en' & Hindi 'hi')
├── media/                         # Uploaded media assets, active model weights (.pt, .onnx)
├── scripts/                       # Operational management and automation scripts
│   ├── compile_locales.py         # Bilingual translation compiler
│   └── verify_live.py             # System verification and smoke test script
├── static/                        # Production and design system static assets
│   ├── css/                       # Design tokens, mobile-first layouts, custom admin theme
│   ├── icons/                     # PWA maskable icons and brand SVGs
│   ├── js/                        # Web Audio API, Spatial Radar, Navigation, Three.js hero
│   └── vendor/                    # Localized vendor dependencies (Three.js r128)
├── templates/                     # Semantic Django HTML templates
│   ├── accounts/                  # Login, Signup, and User Profile templates
│   ├── admin/                     # High-contrast accessible Django admin overrides
│   ├── base.html                  # Base layout with single unified floating pill navigation
│   ├── demo.html                  # Interactive 3D Street Simulator
│   ├── home.html                  # Hero landing page with Three.js canvas & bento cards
│   ├── navigate.html              # Fullscreen camera navigation aid with spatial radar
│   ├── offline.html               # Offline fallback template
│   └── settings.html              # Bento grid assistive settings and emergency contacts
├── tests/                         # Pytest test suite (100% automated test coverage)
└── training/                      # Custom YOLO training, augmentation, and model export
```

---

## Key Modules & Guides

1. **[MOBILE_RESPONSIVE_SYSTEM.md](MOBILE_RESPONSIVE_SYSTEM.md)**: Phone viewport responsiveness, touch targets, bottom navigation bar, and iOS/Android PWA install criteria.
2. **[DEPLOYMENT.md](../DEPLOYMENT.md)**: Production deployment instructions via Docker, Gunicorn/Daphne, and Nginx.
3. **[SECURITY.md](../SECURITY.md)**: Privacy safeguards, authentication models, and vulnerability disclosure.
4. **[PRIVACY.md](../PRIVACY.md)**: Anonymous device merging, on-device inference, and data retention limits.
