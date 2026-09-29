from fastapi import APIRouter, Depends
from app.routes.leads import db_dep

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("")
def list_logs(limit: int = 100, db=Depends(db_dep)):
    limit = max(1, min(limit, 500))
    return [dict(r) for r in db.execute("SELECT * FROM logs ORDER BY created_at DESC,id DESC LIMIT ?", (limit,)).fetchall()]
