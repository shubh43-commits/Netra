# Mobile Responsiveness & Phone Optimization Architecture

Netra is designed primary as an **assistive mobile web application and PWA** held at chest height on smartphones.

---

## 1. Touch Targets & WCAG AAA Accessibility
- All primary interactive buttons (`.btn`, `.chip`, `.mbn-item`) maintain a minimum touch target of **48px x 48px** (exceeding WCAG AAA standards of 44px).
- Input fields enforce `min-height: 52px` and `font-size: 16px` to prevent automatic zoom on iOS Safari.
- High-contrast visual borders (`2px solid #15121f` with 3px–6px solid drop shadows) provide unambiguous distinction for low-vision users.

---

## 2. Phone Navigation System
- **Floating Pill Nav (Desktop / Tablet):**
  - Displays brand identity, calm mode, and full text links (`/demo/`, `/navigate/`, `/settings/`, `/login/` / `👤 <user>`).
- **Tactile Bottom App Bar (Smartphones <= 768px):**
  - Fixed to the bottom viewport with `env(safe-area-inset-bottom)` support.
  - Thumb-accessible 5-tab system:
    1. 🏠 **Home** (`/`)
    2. 🎮 **Demo** (`/demo/`)
    3. 👁️ **Start** (`/navigate/`) — Elevated center pill for immediate activation.
    4. ⚙️ **Settings** (`/settings/`)
    5. 👤 **Profile / Login** (`/profile/` or `/login/`)

---

## 3. High-Contrast Django Admin Panel
- Overrides Django 5 default themes with locked high-contrast CSS tokens:
  - Background: Crisp warm `#f8f5f0`
  - Text: High contrast `#15121f`
  - Table headers: `#ede6dc` with bold headers
  - Buttons: Lime `+ Add` (`#d4f55a`) and lilac `✎ Change` (`#d9ccff`)
- Eliminates desktop-centric margin crushes (`.colMS` right margin reset from 300px to 0).
- Horizontally scrollable data tables on phone viewports with touch momentum scrolling.
- Instant **🌐 View App** header link to return to the mobile application without browser history reliance.
