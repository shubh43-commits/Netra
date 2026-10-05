"""
Tests for Netra Fall Detection, Panic Distress Alerts, and Emergency Links.
Verifies:
- POST /api/incidents/ logging
- WhatsApp link generation with encoded GPS coordinates and Google Maps URL
- SMS link generation
- Contact resolution for registered accounts and anonymous devices
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.accounts.models import Device, EmergencyContact
from apps.analytics.models import SafetyIncident

User = get_user_model()


class SafetyIncidentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="safety_user", password="password123")
        self.device = Device.objects.create()
        self.dev_id = str(self.device.id)

        # Create emergency contacts
        self.contact = EmergencyContact.objects.create(
            device=self.device,
            name="Rahul Sharma",
            phone="+919876543210",
            relationship="family"
        )

    def test_report_incident_and_generate_emergency_links(self):
        """Reporting a fall generates pre-filled WhatsApp & SMS links with GPS coordinates."""
        payload = {
            "incident_type": "fall_detected",
            "latitude": "28.613939",
            "longitude": "77.209021",
            "device_id": self.dev_id
        }

        response = self.client.post(
            reverse('report-incident'),
            payload,
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])

        contacts = data["data"]["emergency_contacts"]
        self.assertEqual(len(contacts), 1)

        c = contacts[0]
        self.assertEqual(c["contact_name"], "Rahul Sharma")
        self.assertIn("919876543210", c["whatsapp_url"])
        self.assertIn("maps.google.com", c["whatsapp_url"])
        self.assertIn("sms:919876543210", c["sms_url"])

        # Verify DB entry
        incident = SafetyIncident.objects.get(id=data["data"]["incident_id"])
        self.assertEqual(incident.incident_type, "fall_detected")
        self.assertAlmostEqual(float(incident.latitude), 28.613939, places=4)
        self.assertFalse(incident.resolved)

    def test_authenticated_user_contacts_used(self):
        """When logged in, user's emergency contacts are used."""
        user_contact = EmergencyContact.objects.create(
            user=self.user,
            name="Priya Patel",
            phone="+919123456789",
            relationship="friend"
        )

        self.client.force_login(self.user)
        payload = {
            "incident_type": "panic_button",
            "latitude": None,
            "longitude": None
        }

        response = self.client.post(
            reverse('report-incident'),
            payload,
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        contacts = response.json()["data"]["emergency_contacts"]
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0]["contact_name"], "Priya Patel")
        self.assertIn("919123456789", contacts[0]["whatsapp_url"])
