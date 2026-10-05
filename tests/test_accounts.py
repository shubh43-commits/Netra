"""
Integration and Unit Tests for Netra Accounts, Auth, Anonymous Devices, and Settings Merge.
"""
import uuid
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from apps.accounts.models import Device, UserSettings, EmergencyContact


class AccountsAndDeviceAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.device_uuid = str(uuid.uuid4())

    def test_anonymous_device_registration(self):
        """Test registering an anonymous device."""
        response = self.client.post(
            reverse('devices-register'),
            data={"device_id": self.device_uuid, "platform": "web", "app_version": "1.0.0"},
            content_type="application/json"
        )
        self.assertIn(response.status_code, [200, 201])
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["id"], self.device_uuid)
        self.assertEqual(response.headers.get("X-Device-Id"), self.device_uuid)

    def test_anonymous_settings_get_and_put(self):
        """Test anonymous client can read and update settings using X-Device-Id."""
        # Read default settings
        res_get = self.client.get(reverse('user-settings'), HTTP_X_DEVICE_ID=self.device_uuid)
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["data"]["language"], "en")

        # Update settings to Hindi and custom speech rate
        update_payload = {
            "language": "hi",
            "speech_rate": 1.5,
            "volume": 0.8,
            "alert_distance_m": 7.0,
            "vibration": True,
            "spatial_beeps": True,
            "low_power": False,
            "calm_mode": True,
            "model_size": "nano",
            "detection_mode": "cloud",
            "fall_detection_enabled": True
        }
        res_put = self.client.put(
            reverse('user-settings'),
            data=update_payload,
            content_type="application/json",
            HTTP_X_DEVICE_ID=self.device_uuid
        )
        self.assertEqual(res_put.status_code, 200)
        saved = res_put.json()["data"]
        self.assertEqual(saved["language"], "hi")
        self.assertEqual(saved["speech_rate"], 1.5)
        self.assertEqual(saved["alert_distance_m"], 7.0)
        self.assertTrue(saved["fall_detection_enabled"])

    def test_settings_safe_ranges_validation(self):
        """Test invalid speech rate or distance is rejected."""
        invalid_payload = {
            "language": "en",
            "speech_rate": 4.0,  # Invalid: > 2.5
            "volume": 2.0,       # Invalid: > 1.0
            "alert_distance_m": 45.0  # Invalid: > 20.0
        }
        res = self.client.put(
            reverse('user-settings'),
            data=invalid_payload,
            content_type="application/json",
            HTTP_X_DEVICE_ID=self.device_uuid
        )
        self.assertEqual(res.status_code, 400)
        errors = res.json()["errors"]
        self.assertIn("speech_rate", errors)
        self.assertIn("volume", errors)
        self.assertIn("alert_distance_m", errors)

    def test_emergency_contact_crud_and_phone_validation(self):
        """Test creating, reading, updating, and phone validation for emergency contacts."""
        # Invalid phone format
        res_invalid = self.client.post(
            reverse('emergency-contacts-list'),
            data={"name": "Aarav", "phone": "9876543210", "relationship": "family"},
            content_type="application/json",
            HTTP_X_DEVICE_ID=self.device_uuid
        )
        self.assertEqual(res_invalid.status_code, 400)

        # Valid E.164 phone number
        res_valid = self.client.post(
            reverse('emergency-contacts-list'),
            data={"name": "Aarav", "phone": "+919876543210", "relationship": "family"},
            content_type="application/json",
            HTTP_X_DEVICE_ID=self.device_uuid
        )
        self.assertEqual(res_valid.status_code, 201)
        contact_id = res_valid.json()["data"]["id"]

        # List contacts
        res_list = self.client.get(
            reverse('emergency-contacts-list'),
            HTTP_X_DEVICE_ID=self.device_uuid
        )
        self.assertEqual(len(res_list.json()["data"]), 1)

        # Delete contact
        res_del = self.client.delete(
            reverse('emergency-contacts-detail', kwargs={"pk": contact_id}),
            HTTP_X_DEVICE_ID=self.device_uuid
        )
        self.assertEqual(res_del.status_code, 200)

    def test_emergency_contact_limit_max_5(self):
        """Ensure an entity cannot exceed 5 emergency contacts."""
        for i in range(5):
            res = self.client.post(
                reverse('emergency-contacts-list'),
                data={"name": f"Contact {i}", "phone": f"+91987654321{i}", "relationship": "friend"},
                content_type="application/json",
                HTTP_X_DEVICE_ID=self.device_uuid
            )
            self.assertEqual(res.status_code, 201)

        # 6th contact must be rejected
        res_6 = self.client.post(
            reverse('emergency-contacts-list'),
            data={"name": "Contact 6", "phone": "+919876543299", "relationship": "other"},
            content_type="application/json",
            HTTP_X_DEVICE_ID=self.device_uuid
        )
        self.assertEqual(res_6.status_code, 400)
        self.assertIn("maximum of 5", str(res_6.json()["errors"]))

    def test_user_registration_login_and_token_refresh(self):
        """Test registration, JWT generation, and token refresh."""
        # 1. Register
        reg_payload = {
            "username": "netra_user_1",
            "email": "user1@example.com",
            "password": "StrongPassword123!",
        }
        res_reg = self.client.post(
            reverse('auth-register'),
            data=reg_payload,
            content_type="application/json"
        )
        self.assertEqual(res_reg.status_code, 201)
        reg_data = res_reg.json()["data"]
        self.assertIn("access", reg_data)
        self.assertIn("refresh", reg_data)

        # 2. Login
        res_login = self.client.post(
            reverse('auth-login'),
            data={"username": "netra_user_1", "password": "StrongPassword123!"},
            content_type="application/json"
        )
        self.assertEqual(res_login.status_code, 200)
        refresh_token = res_login.json()["data"]["refresh"]

        # 3. Refresh Token
        res_refresh = self.client.post(
            reverse('auth-token-refresh'),
            data={"refresh": refresh_token},
            content_type="application/json"
        )
        self.assertEqual(res_refresh.status_code, 200)
        self.assertIn("access", res_refresh.json())

    def test_device_merge_into_user_on_signup(self):
        """
        Verify that settings and emergency contacts created anonymously
        are automatically merged into the user account upon registration.
        """
        # Anonymous device creates Hindi preference & emergency contact
        self.client.put(
            reverse('user-settings'),
            data={"language": "hi", "speech_rate": 1.7, "alert_distance_m": 8.0, "fall_detection_enabled": True},
            content_type="application/json",
            HTTP_X_DEVICE_ID=self.device_uuid
        )
        self.client.post(
            reverse('emergency-contacts-list'),
            data={"name": "Guardian", "phone": "+919988776655", "relationship": "caregiver"},
            content_type="application/json",
            HTTP_X_DEVICE_ID=self.device_uuid
        )

        # User registers with device_id
        res_reg = self.client.post(
            reverse('auth-register'),
            data={
                "username": "migrated_user",
                "password": "SafePassword999!",
                "device_id": self.device_uuid
            },
            content_type="application/json"
        )
        self.assertEqual(res_reg.status_code, 201)
        self.assertTrue(res_reg.json()["data"]["merged_from_device"])

        access_token = res_reg.json()["data"]["access"]

        # Authenticated user fetches settings (without X-Device-Id)
        res_user_settings = self.client.get(
            reverse('user-settings'),
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        user_settings_data = res_user_settings.json()["data"]
        self.assertEqual(user_settings_data["language"], "hi")
        self.assertEqual(user_settings_data["speech_rate"], 1.7)
        self.assertTrue(user_settings_data["fall_detection_enabled"])

        # Authenticated user fetches contacts
        res_user_contacts = self.client.get(
            reverse('emergency-contacts-list'),
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        contacts = res_user_contacts.json()["data"]
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0]["name"], "Guardian")
        self.assertEqual(contacts[0]["phone"], "+919988776655")

    def test_frontend_web_auth_pages_and_flow(self):
        """Verify frontend Login and Sign Up pages render and process user credentials."""
        # 1. Login page renders HTTP 200
        res_login_get = self.client.get(reverse('user-login'))
        self.assertEqual(res_login_get.status_code, 200)
        self.assertContains(res_login_get, "Log In")

        # 2. Signup page renders HTTP 200
        res_signup_get = self.client.get(reverse('user-signup'))
        self.assertEqual(res_signup_get.status_code, 200)
        self.assertContains(res_signup_get, "Create your")

        # 3. User registers via web signup form
        res_signup_post = self.client.post(
            reverse('user-signup'),
            data={
                "username": "web_walk_user",
                "email": "webuser@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!"
            }
        )
        self.assertEqual(res_signup_post.status_code, 302)  # Redirects to / on success
        self.assertTrue(User.objects.filter(username="web_walk_user").exists())

        # 4. Logout flow
        res_logout = self.client.get(reverse('user-logout'))
        self.assertEqual(res_logout.status_code, 302)

        # 5. Web login flow
        res_login_post = self.client.post(
            reverse('user-login'),
            data={
                "username": "web_walk_user",
                "password": "StrongPassword123!"
            }
        )
        self.assertEqual(res_login_post.status_code, 302)  # Redirects on success

    def test_user_profile_view_authenticated_and_unauthenticated(self):
        """Test profile page access for authenticated vs anonymous users."""
        # Unauthenticated: redirects to login with next parameter
        res_anon = self.client.get(reverse('user-profile'))
        self.assertEqual(res_anon.status_code, 302)
        self.assertIn('/login/', res_anon.url)

        # Authenticated user: renders profile with status 200
        user = User.objects.create_user(username="prof_user", password="PassWord123!")
        self.client.login(username="prof_user", password="PassWord123!")
        res_auth = self.client.get(reverse('user-profile'))
        self.assertEqual(res_auth.status_code, 200)
        self.assertContains(res_auth, "prof_user")
        self.assertContains(res_auth, "Assistive Audio & Haptics")

    def test_login_page_shows_active_profile_when_authenticated(self):
        """When an authenticated user visits /login/, it renders their active profile status card."""
        user = User.objects.create_user(username="active_runner", email="runner@example.com", password="PassWord123!")
        self.client.login(username="active_runner", password="PassWord123!")

        res = self.client.get(reverse('user-login'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "active_runner")
        self.assertContains(res, "Assistive User Account Active")
        self.assertContains(res, "View Full Profile")

    def test_web_login_failure_displays_error_and_preserves_username(self):
        """Invalid web credentials safely re-renders the form with error banner and preserved username."""
        res = self.client.post(
            reverse('user-login'),
            data={
                "username": "usre1",
                "password": "wrongpassword123"
            }
        )
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Invalid username or password")
        self.assertContains(res, 'value="usre1"')



