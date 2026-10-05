"""
Business logic services for Netra Accounts.
Handles:
- Anonymous device identification and creation
- Seamless merge of anonymous settings and emergency contacts into registered user accounts
"""
import uuid
from typing import Optional, Tuple
from django.contrib.auth.models import User
from django.db import transaction

from .models import Device, UserSettings, EmergencyContact


def get_or_create_device(
    device_id_str: Optional[str],
    user: Optional[User] = None,
    platform: str = "web",
    app_version: str = "1.0.0"
) -> Tuple[Device, bool]:
    """
    Retrieves or initializes a Device record.
    If no valid UUID is passed, generates a new one.
    """
    device_uuid = None
    if device_id_str:
        try:
            device_uuid = uuid.UUID(str(device_id_str).strip())
        except (ValueError, AttributeError):
            device_uuid = uuid.uuid4()
    else:
        device_uuid = uuid.uuid4()

    device, created = Device.objects.get_or_create(
        id=device_uuid,
        defaults={
            "user": user,
            "platform": platform,
            "app_version": app_version,
        }
    )

    if not created:
        if user and not device.user:
            device.user = user
        device.record_activity()

    # Ensure device has a default UserSettings record
    if not hasattr(device, "settings") or not device.settings:
        UserSettings.objects.get_or_create(device=device)

    return device, created


@transaction.atomic
def merge_device_into_user(device_or_id, user: User) -> bool:
    """
    Merges anonymous device preferences and emergency contacts into the user's account.
    Called automatically during registration and login. Accepts Device model instance or UUID/str.
    """
    if not device_or_id:
        return False

    if isinstance(device_or_id, Device):
        device = device_or_id
    else:
        try:
            device_uuid = uuid.UUID(str(device_or_id).strip())
            device = Device.objects.select_for_update().filter(id=device_uuid).first()
        except (ValueError, AttributeError):
            return False

    if not device:
        return False

    # 1. Associate device with user
    device.user = user
    device.save(update_fields=["user"])

    # 2. Merge UserSettings
    device_settings = UserSettings.objects.filter(device=device).first()
    user_settings = UserSettings.objects.filter(user=user).first()

    if device_settings and not user_settings:
        # Transfer the device's settings to the user
        device_settings.user = user
        device_settings.device = None
        device_settings.save(update_fields=["user", "device"])
    elif device_settings and user_settings:
        # Merge device values if device settings were updated more recently
        if device_settings.updated_at > user_settings.updated_at:
            for field in [
                "language", "speech_rate", "volume", "spatial_beeps",
                "alert_distance_m", "vibration", "low_power", "calm_mode",
                "model_size", "detection_mode", "fall_detection_enabled"
            ]:
                setattr(user_settings, field, getattr(device_settings, field))
            user_settings.save()
        # Clean up the redundant device settings
        device_settings.delete()
    elif not user_settings:
        # Initialize default user settings if neither existed
        UserSettings.objects.create(user=user)

    # 3. Merge EmergencyContacts (respecting max 5 contacts limit and deduplicating phone numbers)
    existing_user_phones = set(
        EmergencyContact.objects.filter(user=user).values_list("phone", flat=True)
    )
    current_user_count = len(existing_user_phones)

    device_contacts = EmergencyContact.objects.filter(device=device)
    for contact in device_contacts:
        if current_user_count >= 5:
            # Stop if user reached maximum limit of 5 contacts
            break
        if contact.phone not in existing_user_phones:
            contact.user = user
            contact.device = None
            contact.save(update_fields=["user", "device"])
            existing_user_phones.add(contact.phone)
            current_user_count += 1
        else:
            # Duplicate contact, delete redundant entry
            contact.delete()

    return True
