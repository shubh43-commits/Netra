"""
Validators for Netra Accounts app:
- E.164 phone number format validation
- Safe range validators for assistive user settings
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# ITU-T E.164 standard regex: starts with '+', followed by 1-15 digits
E164_REGEX = re.compile(r'^\+[1-9]\d{1,14}$')


def validate_e164_phone(value: str) -> None:
    """
    Validates that a phone number adheres to the E.164 international standard.
    Example valid: +919876543210, +14155552671
    """
    if not value or not E164_REGEX.match(value.strip()):
        raise ValidationError(
            _("Phone number must be in valid E.164 international format (e.g., +919876543210)."),
            code="invalid_e164"
        )


def validate_speech_rate(value: float) -> None:
    if value < 0.5 or value > 2.5:
        raise ValidationError(
            _("Speech rate must be between 0.5x and 2.5x."),
            code="invalid_speech_rate"
        )


def validate_volume(value: float) -> None:
    if value < 0.0 or value > 1.0:
        raise ValidationError(
            _("Volume must be between 0.0 (mute) and 1.0 (maximum)."),
            code="invalid_volume"
        )


def validate_alert_distance(value: float) -> None:
    if value < 0.5 or value > 20.0:
        raise ValidationError(
            _("Alert distance must be between 0.5 meters and 20.0 meters."),
            code="invalid_alert_distance"
        )
