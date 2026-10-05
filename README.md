# Netra (नेत्र): Your Phone Just Got Eyes

> **Assistive Orientation, Obstacle Detection & Spatial Audio Guidance Aid for the Visually Impaired**  
> Built for hackathons, community impact, and accessible mobility.

---

## ⚠️ Safety Disclaimer
**Netra is an assistive aid that complements a cane or guide dog. Distance estimates are approximate.** Users must always remain attentive to their surroundings and use their physical white cane as their primary mobility tool.

---

## 🎨 Design System & Visual Philosophy
The user interface is built on Netra's modern, light, playful, and tactile aesthetic:
- **Colours:** Cream background (`#f5efe6`), Ink text/borders (`#15121f`), Muted text (`#5f5a6e`), Electric Violet (`#5b3df5`), Lilac (`#d9ccff`), Lime (`#d4f55a`), Pink (`#ffc2dc`), Peach (`#ffd9b8`), Sky (`#c6e6ff`).
- **Typography:** **Bricolage Grotesque** (800 weight, tight letter-spacing) for display titles & headings; **Atkinson Hyperlegible** for clean body text.
- **Shapes & Accents:** Very rounded cards (`28px` radius), `2px` ink borders, hard offset drop-shadows (`6px 6px 0` / `8px 8px 0 var(--ink)`), floating pill navigation, sticker badges rotated slightly.
- **Components:** Floating pill nav, hero with highlighted word and live speech-bubble alert, tilted dark marquee strip, bento grid of colourful tiles, numbered step cards, violet stats panel, and prominent call-to-action buttons.
- **3D Hero Scene (Three.js r128):** Real-time echolocation scene with violet sound-wave rings rolling outward and coloured hazard markers (ink pillar, coloured sphere with ink outline) popping up dynamically as sound waves reach them. Includes cursor and device gyroscope tilt reaction, Calm Mode toggle, and `prefers-reduced-motion` compliance.

---

## 🏗️ Architecture & Technology Stack
- **Backend:** Python 3.11+, Django 5+, Django REST Framework, Channels, Daphne ASGI server.
- **Settings Split:** `config/settings/base.py`, `dev.py` (SQLite, in-memory channels), `prod.py` (PostgreSQL, Redis).
- **Frontend:** Pure Django templates, modular CSS (`static/css/netra.css`), vanilla ES modules, static vendor Three.js (`static/vendor/three.min.js`), no npm / Webpack / Vite build steps required.
- **PWA & Offline:** Root Service Worker (`/sw.js`), Web App Manifest (`/manifest.webmanifest`), violet & lime palette icons, and a dedicated offline page.
- **Accessibility:** Screen-reader friendly (TalkBack & VoiceOver), skip-to-content link, 64px+ touch targets, high contrast, ARIA live status bubbles.
- **Languages:** English and हिन्दी (Hindi) with a pill language switcher in the navigation.

---

## 📁 Project Structure

```text
NetraAI/
├── config/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── asgi.py
│   ├── celery.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── core/                    # Core views (Home, Navigate, Demo, Offline, PWA)
│   └── accounts/                # User accounts & settings sync skeleton
├── templates/
│   ├── base.html                # Floating pill nav, language switcher, footer
│   ├── home.html                # Hero, 3D echolocation, marquee, bento, steps, stats
│   ├── navigate.html            # Live camera navigation view
│   ├── demo.html                # Street simulation demo view
│   └── offline.html             # Offline fallback view
├── static/
│   ├── css/
│   │   └── netra.css            # Single unified design system CSS
│   ├── js/
│   │   ├── hero3d.js            # Three.js echolocation hero scene
│   │   └── home.js              # Speech-bubble alert cycling & scroll reveals
│   ├── vendor/
│   │   └── three.min.js         # Three.js r128 served locally
│   ├── icons/
│   │   ├── icon.svg             # Violet & lime vector icon
│   │   ├── icon-192.png         # 192px PWA icon
│   │   └── icon-512.png         # 512px PWA icon
│   ├── manifest.webmanifest     # Web App Manifest
│   └── sw.js                    # Service worker script
├── locale/
│   ├── en/LC_MESSAGES/django.po
│   └── hi/LC_MESSAGES/django.po
├── scripts/
│   └── compile_locales.py       # Zero-dependency PO -> MO compiler
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🚀 How to Run Locally

### 1. Prerequisites
- Python 3.11+
- Virtual environment (`venv`)

### 2. Setup Virtual Environment & Dependencies
```powershell
# Activate your virtual environment
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 3. Compile Language Catalogs (English & Hindi)
```powershell
python scripts/compile_locales.py
```

### 4. Apply Database Migrations
```powershell
python manage.py migrate
```

### 5. Start the Daphne ASGI Development Server
```powershell
python manage.py runserver
# or directly via Daphne:
daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

Open your browser to: **http://127.0.0.1:8000/**

---

## 🐳 Docker Deployment
To run with PostgreSQL and Redis via Docker Compose:
```bash
docker-compose up --build
```
The application will be accessible at **http://localhost:8000/**.

---

## 🔍 Visual Verification Checklist (Stage 1)
When you load the app at `http://127.0.0.1:8000/`, check:
1. **Design System & Palette:**
   - Background is light cream `#f5efe6` (NOT dark mode).
   - Headings render in bold Bricolage Grotesque.
   - 28px card radiuses and 6px / 8px ink hard offset shadows.
2. **Floating Pill Nav:**
   - Frosted glass floating pill with `netra.` brand, nav links, language switch, Calm Mode, and Start button.
   - Links navigate smoothly to sections (`#features`, `#how`, `#impact`).
3. **3D Echolocation Hero Scene:**
   - Expanding violet sound waves roll outward across the floor.
   - Coloured hazard spheres on ink pillars pop up as waves touch them.
   - Parallax moves gently when moving your mouse or tilting mobile device.
   - Clicking **"Calm mode"** pauses the animation; clicking again resumes it.
4. **Live Speech-Bubble Alert:**
   - Displays cycling hazard alerts ("All clear ahead.", "Person, ahead, 4 metres.", etc.) with pulsing violet indicator.
5. **Marquee & Bento Grid:**
   - Tilted dark marquee rotates continuously.
   - Bento grid cards (`a` to `f`) display in pastel tones with hover lift.
6. **Bilingual Language Switcher:**
   - Click **"हिन्दी"** in the nav: all headings, badges, descriptions, marquee texts, and cycling speech bubbles switch to Hindi seamlessly.
   - Click **"EN"** to switch back to English.
7. **PWA & Offline:**
   - Open browser DevTools > Application: Service worker `sw.js` is registered at root scope `/`.
   - Manifest `manifest.webmanifest` is loaded with theme `#f5efe6` and violet/lime icons.
   - Simulate offline in DevTools Network tab and reload: `/offline/` loads cleanly in the exact design.
# Netra
