import json
from fastapi import Request
from sqlalchemy.orm import Session

from src.database.models import AuditLog

def write_audit(
    db: Session,
    request: Request,
    user_id,
    action: str,
    entity: str = "file",
    entity_id: str | None = None,
    meta: dict | None = None,
):
    db.add(AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        meta=meta,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    ))
    db.commit()
