"""
Helper Utilities
أدوات مساعدة عامة
"""

import re
import html
import uuid
from typing import Any, Optional
from unicodedata import normalize


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


def slugify(text: str, max_length: int = 100) -> str:
    """
    Convert text to URL-friendly slug.
    تحويل النص إلى slug صديق للروابط
    """
    # Normalize unicode
    text = normalize("NFKD", text)

    # Convert to lowercase
    text = text.lower()

    # Replace Arabic characters with transliteration (basic)
    arabic_map = {
        "ا": "a", "ب": "b", "ت": "t", "ث": "th", "ج": "j",
        "ح": "h", "خ": "kh", "د": "d", "ذ": "th", "ر": "r",
        "ز": "z", "س": "s", "ش": "sh", "ص": "s", "ض": "d",
        "ط": "t", "ظ": "z", "ع": "a", "غ": "gh", "ف": "f",
        "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",
        "ه": "h", "و": "w", "ي": "y", "ء": "", "ة": "h",
        "ى": "a", "أ": "a", "إ": "i", "آ": "a", "ؤ": "w",
        "ئ": "y",
    }
    for ar, en in arabic_map.items():
        text = text.replace(ar, en)

    # Replace spaces and special chars with hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)

    # Remove leading/trailing hyphens
    text = text.strip("-")

    # Limit length
    return text[:max_length]


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input.
    تنظيف مدخلات المستخدم
    """
    if not text:
        return ""

    # Strip whitespace
    text = text.strip()

    # Escape HTML
    text = html.escape(text)

    # Remove null bytes
    text = text.replace("\x00", "")

    # Limit length
    if max_length:
        text = text[:max_length]

    return text


def mask_email(email: str) -> str:
    """Mask email for privacy."""
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"**@{domain}"
    return f"{local[0]}***{local[-1]}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone number for privacy."""
    if len(phone) < 4:
        return "***"
    return f"***{phone[-4:]}"


def format_area(hectares: float, unit: str = "hectares") -> str:
    """Format area with appropriate unit."""
    if unit == "hectares":
        return f"{hectares:.2f} هكتار"
    elif unit == "dunums":
        return f"{hectares * 10:.2f} دونم"
    elif unit == "sq_meters":
        return f"{hectares * 10000:.0f} م²"
    return f"{hectares:.2f}"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values."""
    if old_value == 0:
        return 100.0 if new_value > 0 else 0.0
    return ((new_value - old_value) / abs(old_value)) * 100


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
