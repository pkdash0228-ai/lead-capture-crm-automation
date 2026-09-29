import csv
import io
import sqlite3
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from app.crud import DuplicateLeadError, LeadValidationError, process_lead, update_lead
from app.database import connect, log_event
from app.schemas import LeadInput, LeadUpdate

router = APIRouter(prefix="/api/leads", tags=["leads"])

def db_dep():
    db = connect()
    try: yield db
    finally: db.close()

@router.post("")
def create_lead(payload: LeadInput, db: sqlite3.Connection = Depends(db_dep)):
    try: return process_lead(db, payload.model_dump(), "Website")
    except LeadValidationError as e: raise HTTPException(422, str(e))
    except DuplicateLeadError as e: raise HTTPException(409, str(e))

@router.get("")
def list_leads(q: str | None = None, status: str | None = None, db: sqlite3.Connection = Depends(db_dep)):
    sql, params = "SELECT * FROM leads WHERE 1=1", []
    if q:
        sql += " AND (name LIKE ? OR email LIKE ? OR company LIKE ?)"; params += [f"%{q}%"] * 3
    if status: sql += " AND status=?"; params.append(status)
    sql += " ORDER BY created_at DESC"
    return [dict(row) for row in db.execute(sql, params).fetchall()]

@router.get("/{lead_id}")
def get_lead(lead_id: int, db: sqlite3.Connection = Depends(db_dep)):
    row = db.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    if row is None: raise HTTPException(404, "Lead not found.")
    return dict(row)

@router.patch("/{lead_id}")
def patch_lead(lead_id: int, payload: LeadUpdate, db: sqlite3.Connection = Depends(db_dep)):
    try: result = update_lead(db, lead_id, payload.model_dump(exclude_unset=True))
    except LeadValidationError as e: raise HTTPException(422, str(e))
    except DuplicateLeadError as e: raise HTTPException(409, str(e))
    if result is None: raise HTTPException(404, "Lead not found.")
    return result

@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: sqlite3.Connection = Depends(db_dep)):
    if db.execute("SELECT 1 FROM leads WHERE id=?", (lead_id,)).fetchone() is None: raise HTTPException(404, "Lead not found.")
    log_event(db, "lead_deleted", "success", "Lead deleted.", lead_id)
    db.execute("DELETE FROM leads WHERE id=?", (lead_id,)); db.commit()
    return {"message": "Lead deleted."}

@router.post("/import")
async def import_csv(file: UploadFile = File(...), db: sqlite3.Connection = Depends(db_dep)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Upload a .csv file.")
    try: text = (await file.read()).decode("utf-8-sig")
    except UnicodeDecodeError: raise HTTPException(400, "CSV must use UTF-8 encoding.")
    try:
        reader = csv.DictReader(io.StringIO(text))
        required = {"name", "email", "company", "message"}
        if not reader.fieldnames or not required.issubset({h.strip().lower() for h in reader.fieldnames}):
            raise HTTPException(400, "CSV headers must include name,email,company,message.")
        # Normalize header names so harmless capitalization/spaces are accepted.
        reader = csv.DictReader(io.StringIO(text))
        totals = {"total_rows": 0, "successfully_imported": 0, "duplicates": 0, "invalid_rows": 0, "failed_rows": 0, "row_errors": []}
        for index, row in enumerate(reader, start=2):
            totals["total_rows"] += 1
            row = {str(k).strip().lower(): v for k, v in row.items() if k is not None}
            try:
                process_lead(db, row, "CSV")
                totals["successfully_imported"] += 1
            except DuplicateLeadError as exc:
                totals["duplicates"] += 1; totals["row_errors"].append({"row": index, "error": str(exc)})
            except LeadValidationError as exc:
                totals["invalid_rows"] += 1; totals["row_errors"].append({"row": index, "error": str(exc)})
            except Exception as exc:
                totals["failed_rows"] += 1
                log_event(db, "csv_row", "failed", f"Row {index}: {exc}"); db.commit()
                totals["row_errors"].append({"row": index, "error": "Unexpected processing error."})
        log_event(db, "csv_import", "success", f"Imported {totals['successfully_imported']} of {totals['total_rows']} rows."); db.commit()
        return totals
    except csv.Error as exc:
        log_event(db, "csv_import", "failed", f"Invalid CSV: {exc}"); db.commit()
        raise HTTPException(400, "Could not parse CSV file.")
