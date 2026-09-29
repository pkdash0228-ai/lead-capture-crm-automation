from fastapi import APIRouter, Depends
from app.routes.leads import db_dep
from app.validation import STATUSES

router = APIRouter(tags=["dashboard"])

@router.get("/api/stats")
def stats(db=Depends(db_dep)):
    total = db.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    result = {"total_leads": total}
    for status in STATUSES:
        result[f"{status.lower()}_leads"] = db.execute("SELECT COUNT(*) FROM leads WHERE status=?", (status,)).fetchone()[0]
    result["website_leads"] = db.execute("SELECT COUNT(*) FROM leads WHERE source='Website'").fetchone()[0]
    result["csv_leads"] = db.execute("SELECT COUNT(*) FROM leads WHERE source='CSV'").fetchone()[0]
    result["chatbot_leads"] = db.execute("SELECT COUNT(*) FROM leads WHERE source='Chatbot'").fetchone()[0]
    result["duplicate_count"] = db.execute("SELECT COUNT(*) FROM logs WHERE action='duplicate'").fetchone()[0]
    result["invalid_count"] = db.execute("SELECT COUNT(*) FROM logs WHERE status='invalid'").fetchone()[0]
    return result
