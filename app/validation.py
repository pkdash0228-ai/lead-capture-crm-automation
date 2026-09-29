import re
from typing import Any

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
REQUIRED = ("name", "email", "company", "message")
STATUSES = ("New", "Contacted", "Qualified", "Converted", "Lost")


def normalize_email(value: Any) -> str:
    return str(value or "").strip().lower()


def validate_lead(data: dict[str, Any]) -> tuple[dict[str, str] | None, str | None]:
    cleaned = {key: str(data.get(key) or "").strip() for key in REQUIRED}
    missing = [key for key, value in cleaned.items() if not value]
    if missing:
        return None, "Required fields missing: " + ", ".join(missing)
    cleaned["email"] = normalize_email(cleaned["email"])
    if not EMAIL_RE.fullmatch(cleaned["email"]):
        return None, "Enter a valid email address."
    return cleaned, None
