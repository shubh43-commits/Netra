# Netra AI - Privacy by Design Architecture

Assistive technology must prioritize user trust above all else. For a visually impaired individual navigating streets, homes, or workplaces, camera feeds could capture personal spaces, passerby faces, documents, or private environments.

Netra is architected from the ground up on the principle of **Zero Surveillance & Ephemeral Computing**.

---

## 1. Core Privacy Guarantees

### 1.1 In-Memory Ephemeral Camera Processing
* When you point your camera forward in **Live Navigation Mode (`/navigate/`)**, video frames are processed **strictly in volatile system memory (RAM)**.
* Frames sent across the WebSocket (`/ws/detect/`) are decoded via `io.BytesIO`, evaluated by YOLO, and **destroyed immediately**.
* **Zero video frames are saved to disk, logged to databases, or cached on the server.**

### 1.2 Zero-Barrier Anonymous Use
* You do not need to create an account, provide an email address, or provide a phone number to use Netra.
* Devices are identified by an anonymous random UUID stored in `localStorage`.
* When an anonymous user chooses to register later, preferences and emergency contacts are merged cleanly without linking historical browsing.

### 1.3 Feedback Frames: 90-Day Automatic Purge
* If a user encounters an obstacle that Netra missed and clicks **"Report Bug / Wrong Detection"**, that specific frame is uploaded to assist model retraining.
* Uploaded report frames are:
  1. Stored under randomized, unguessable filenames (`reports/<uuid>.jpg`).
  2. Never linked to public search engines.
  3. **Permanently deleted after 90 days** by an automated Celery background worker (`purge_expired_feedback_reports`).

### 1.4 Opt-In Anonymous Telemetry
* Netra does **not** track your movements or routes.
* High-level performance metrics (session count, average FPS, latency) are collected **only if the user explicitly enables "Analytics Opt-In"** in settings.
* Raw telemetry events are automatically purged after 30 days.

### 1.5 Emergency Distress Contacts
* Emergency contact names and phone numbers are stored solely to construct device-side WhatsApp and SMS alert links (`https://wa.me/...` and `sms:...`).
* Location data is only attached when a fall or panic alert is triggered, and is dispatched directly through the user's chosen messaging app.

---

## 2. Privacy Architecture Summary

| Data Category | Collection Trigger | Storage Location | Retention Period | Third-Party Sharing |
| :--- | :--- | :--- | :--- | :--- |
| **Live Camera Video** | User walking | Volatile RAM only | 0 milliseconds | **None** |
| **Spoken Speech / Beeps** | Local browser | Client device only | Ephemeral | **None** |
| **Bug Report Frames** | Explicit user report | Encrypted server storage | **90 days max** (auto-purged) | **None** |
| **GPS Coordinates** | Fall or SOS trigger | Ephemeral incident log | User-controlled | Only contacts via WhatsApp/SMS |
| **Device Preferences** | Settings change | Client `localStorage` / DB | Until cleared | **None** |

---

## 3. Compliance & Standards

Netra is designed in accordance with the principles of:
* **GDPR (General Data Protection Regulation)**: Data minimization, purpose limitation, storage limitation (90-day purge).
* **Digital Personal Data Protection Act (DPDP Act, India)**: Explicit opt-in consent for telemetry, zero dark patterns, accessible disclosure.
