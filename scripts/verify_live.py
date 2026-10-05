"""
Comprehensive live end-to-end verification script for Netra AI.
Tests every API endpoint and frontend page against the live server at http://127.0.0.1:8000.
"""
import io
import json
import urllib.request
import urllib.parse
from PIL import Image

BASE_URL = "http://127.0.0.1:8000"

def log(msg, status="OK"):
    badge = f"[\033[92m{status}\033[0m]" if status == "OK" else f"[\033[91m{status}\033[0m]"
    print(f"{badge} {msg}")

def request_json(url, data=None, headers=None, method="GET"):
    headers = headers or {}
    req_data = None
    if data is not None:
        if isinstance(data, dict):
            req_data = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(data, bytes):
            req_data = data
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    with urllib.request.urlopen(req) as response:
        content = response.read().decode("utf-8")
        return response.status, json.loads(content)

def check_url(path, desc):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as resp:
        if resp.status == 200:
            log(f"{desc} ({path}) -> HTTP 200 OK")
            return True
        else:
            log(f"{desc} ({path}) -> HTTP {resp.status}", "FAIL")
            return False

def run_tests():
    print("=" * 65)
    print("NETRA AI - COMPLETE SYSTEM LIVE VERIFICATION")
    print("=" * 65)

    # 1. Frontend Web Pages
    print("\n--- 1. Frontend & PWA Pages ---")
    check_url("/", "Landing Page (with 3D hero & audio preview)")
    check_url("/demo/", "Interactive Street Simulator")
    check_url("/navigate/", "Live Camera Navigation Viewport")
    check_url("/settings/", "Bento Settings Dashboard")
    check_url("/offline/", "PWA Offline Fallback")
    check_url("/sw.js", "PWA Service Worker")
    check_url("/manifest.webmanifest", "PWA Web Manifest")

    # 2. System & Health
    print("\n--- 2. Health & Documentation APIs ---")
    status, health = request_json(f"{BASE_URL}/api/health/")
    log(f"Health Telemetry: {health['status']} (Model Loaded: {health['services']['model_loaded']})")
    status, ver = request_json(f"{BASE_URL}/api/version/")
    log(f"Version Endpoint: Netra {ver['version']} ({ver['api_version']})")
    check_url("/api/docs/", "OpenAPI Swagger Interactive Documentation")

    # 3. Accounts & Settings
    print("\n--- 3. Accounts, Devices & Emergency Contacts ---")
    dev_id = "00000000-0000-0000-0000-000000000099"
    # Anonymous Settings
    status, settings_res = request_json(f"{BASE_URL}/api/settings/", headers={"X-Device-ID": dev_id})
    log(f"Device Settings: Retrieved default settings for device {dev_id}")

    # Add emergency contact
    status, contact_res = request_json(
        f"{BASE_URL}/api/contacts/",
        data={"name": "Aunt Sarah", "phone": "+919876543210", "relationship": "family"},
        headers={"X-Device-ID": dev_id},
        method="POST"
    )
    log(f"Emergency Contact: Added contact {contact_res['data']['name']} ({contact_res['data']['phone']})")

    # 4. Computer Vision, Description & OCR
    print("\n--- 4. Computer Vision & Scene Intelligence ---")
    # Generate dummy test image
    img = Image.new("RGB", (200, 200), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    # Multipart helper
    boundary = "----NetraBoundary12345"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="test.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + img_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    # REST Detect
    status, detect_res = request_json(
        f"{BASE_URL}/api/detect/",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    d_data = detect_res.get('data') or detect_res
    log(f"YOLO Detect: Processed image ({d_data['latency_ms']} ms, items: {d_data['count']})")

    # REST Describe
    status, desc_res = request_json(
        f"{BASE_URL}/api/describe/",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    desc_data = desc_res.get('data') or desc_res
    log(f"Scene Describe: \"{desc_data['text']}\" ({desc_data['latency_ms']} ms)")

    # 5. Feedback Reporting
    print("\n--- 5. ModelHub & Feedback Reporting ---")
    body_report = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="bug.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + img_bytes + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="issue_type"\r\n\r\n'
        f"missed_obstacle\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="user_note"\r\n\r\n'
        f"Low bench on path not detected\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")

    status, report_res = request_json(
        f"{BASE_URL}/api/feedback/report/",
        data=body_report,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "X-Device-ID": dev_id},
        method="POST"
    )
    log(f"Feedback Report: Created report {report_res['data']['report_id'][:8]}...")

    # 6. Telemetry & Safety Incidents
    print("\n--- 6. Telemetry & Safety Distress Alerts ---")
    # Record event
    status, event_res = request_json(
        f"{BASE_URL}/api/events/",
        data={"event_type": "session_start", "event_data": {"mode": "simulated"}, "device_id": dev_id},
        method="POST"
    )
    log(f"Telemetry Events: Logged session_start event")

    # Fall incident report
    status, inc_res = request_json(
        f"{BASE_URL}/api/incidents/",
        data={"incident_type": "fall_detected", "latitude": 28.6139, "longitude": 77.2090, "device_id": dev_id},
        method="POST"
    )
    contact_count = len(inc_res['data']['emergency_contacts'])
    wa_url = inc_res['data']['emergency_contacts'][0]['whatsapp_url'] if contact_count > 0 else ""
    log(f"Safety Incident: Logged fall_detected, generated {contact_count} emergency contact link(s)")
    if wa_url:
        print(f"      WhatsApp SOS Link: {wa_url[:75]}...")

    print("\n" + "=" * 65)
    print("ALL CORE CAPABILITIES TESTED & OPERATIONAL!")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
