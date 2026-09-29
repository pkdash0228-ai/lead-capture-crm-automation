import sqlite3
from typing import Any
from app.database import log_event
from app.email_service import send_lead_emails
from app.validation import STATUSES, validate_lead


class LeadValidationError(Exception): pass
class DuplicateLeadError(Exception): pass


def process_lead(db: sqlite3.Connection, payload: dict[str, Any], source: str) -> dict:
    clean, error = validate_lead(payload)
    if error:
        log_event(db, "validation", "invalid", error)
        db.commit()
        raise LeadValidationError(error)
    try:
        cur = db.execute("INSERT INTO leads(name,email,company,message,source) VALUES(?,?,?,?,?)",
                         (clean["name"], clean["email"], clean["company"], clean["message"], source))
    except sqlite3.IntegrityError:
        existing = db.execute("SELECT id FROM leads WHERE email=? COLLATE NOCASE", (clean["email"],)).fetchone()
        log_event(db, "duplicate", "skipped", f"Duplicate email: {clean['email']}", existing["id"] if existing else None)
        db.commit()
        raise DuplicateLeadError("A lead with this email already exists.")
    lead_id = cur.lastrowid
    log_event(db, "lead_created", "success", f"Lead created from {source}.", lead_id)
    lead = dict(db.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone())
    for action, ok, message in send_lead_emails(lead):
        log_event(db, action, "success" if ok else "failed", message, lead_id)
    db.commit()
    return lead


def update_lead(db: sqlite3.Connection, lead_id: int, changes: dict[str, Any]) -> dict | None:
    row = db.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    if row is None: return None
    fields = {k: v for k, v in changes.items() if v is not None}
    allowed = {"name", "email", "company", "message", "status"}
    if set(fields) - allowed: raise LeadValidationError("Unsupported lead field.")
    if fields.get("status") and fields["status"] not in STATUSES:
        raise LeadValidationError("Status must be New, Contacted, Qualified, Converted, or Lost.")
    if "email" in fields:
        fields["email"] = str(fields["email"]).strip().lower()
    for key in ("name", "company", "message"):
        if key in fields:
            fields[key] = str(fields[key]).strip()
            if not fields[key]: raise LeadValidationError(f"{key.title()} cannot be empty.")
    if fields:
        assignments = ",".join(f"{k}=?" for k in fields)
        try: db.execute(f"UPDATE leads SET {assignments}, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?", (*fields.values(), lead_id))
        except sqlite3.IntegrityError: raise DuplicateLeadError("A lead with this email already exists.")
        log_event(db, "lead_updated", "success", "Lead updated.", lead_id)
        db.commit()
    return dict(db.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone())
