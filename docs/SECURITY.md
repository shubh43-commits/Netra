# Netra AI - Security Architecture & Policy

This document outlines the security architecture, threat model mitigations, and configuration rules enforced in the Netra AI assistive vision platform.

---

## 1. Threat Model & Mitigations

| Threat | Risk | Mitigation in Netra |
| :--- | :--- | :--- |
| **Video Camera Snoop / Data Leak** | Critical | **Zero Disk Persistence:** Video frames streamed to `/ws/detect/` are processed exclusively in RAM (`io.BytesIO`) and deleted immediately after inference. Frames are never written to disk, database, or logs. |
| **Malicious File Upload / Exploit** | High | Uploaded frames are validated using Pillow `img.verify()`, inspected for binary magic bytes (`\xff\xd8\xff`), restricted in size (max 5 MB for reports, 2 MB for REST detect), and assigned unguessable UUID filenames (`reports/<uuid>.jpg`). |
| **Denial of Service (DoS) via Video Stream** | High | WebSocket streams enforce **15 FPS max rate limiting**, **300 KB max frame size**, **max 2 concurrent connections per device ID**, and an **automatic 120s idle timeout**. |
| **Unauthorized Telemetry Harvesting** | High | Telemetry requires explicit `analytics_opt_in=True`. All usage events are decoupled from user PII, and raw rows are purged automatically after 30 days via Celery beat. |
| **Credential Theft / Session Hijacking** | Medium | JWT access tokens expire in 2 hours. Cookies enforce `HttpOnly`, `SameSite=Lax`, and `Secure` over HTTPS. |

---

## 2. Production Security Settings (`config/settings/prod.py`)

In production environments (`DJANGO_SETTINGS_MODULE=config.settings.prod`), the following settings are strictly enforced:

```python
# HTTPS Enforcement
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie Hardening
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# Browser Defenses
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

---

## 3. API Throttling & Rate Limits

Netra configures Django REST Framework throttling tiers:

* **Anonymous Users**: `120 requests/minute`
* **Authenticated Accounts**: `600 requests/minute`
* **Bug Reports (`/api/feedback/report/`)**: `10 requests/hour` per device to prevent storage flooding.

---

## 4. WebSocket Defense-in-Depth (`/ws/detect/`)

1. **Protocol Handshake**: Connections must send a JSON `{"type": "start"}` frame before binary frames are accepted.
2. **Magic Bytes Validation**: Binary frames must start with JPEG magic bytes `b'\xff\xd8\xff'`. Any non-JPEG payload is immediately rejected.
3. **Memory Isolation**: Frames are decoded into NumPy arrays in a thread pool executor and released immediately upon response generation.
4. **Per-Device Concurrency**: Devices are limited to a maximum of 2 concurrent WebSocket sessions. Additional connections receive close code `4003`.

---

## 5. Vulnerability Reporting

If you discover a security vulnerability in Netra, please report it privately by emailing `security@netra-ai.org` or creating a confidential GitHub security advisory. Please do not publish issues publicly until a patch has been released.
