from datetime import datetime, timedelta, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database.get_db import get_db
from src.database.models import User, AuditLog, FileComment
from src.auth.dependencies import get_current_user
from src.database.schemas import UserActiveUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/me")
def get_admin_me(current_user: User = Depends(get_current_user)):
    return {"is_superuser": current_user.is_superuser}


@router.get("/users/stats")
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    total = db.query(User).count()
    active = db.query(User).filter(User.is_active.is_(True)).count()
    superusers = db.query(User).filter(User.is_superuser.is_(True)).count()
    inactive = total - active

    return {
        "total_users": total,
        "active_users": active,
        "inactive_users": inactive,
        "superusers": superusers,
    }


@router.get("/users")
def list_users(
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    start_date = (datetime.now(timezone.utc) - timedelta(days=days - 1)).date()
    day_list = [start_date + timedelta(days=i) for i in range(days)]
    day_strs = [d.isoformat() for d in day_list]

    users = db.query(User).order_by(User.created_at.desc()).all()
    user_ids = [u.id for u in users]

    last_login_rows = (
        db.query(AuditLog.user_id, func.max(AuditLog.created_at))
        .filter(AuditLog.action == "login", AuditLog.user_id.in_(user_ids))
        .group_by(AuditLog.user_id)
        .all()
    )
    last_login_map = {uid: dt for uid, dt in last_login_rows}

    download_rows = (
        db.query(AuditLog.user_id, func.count(AuditLog.id))
        .filter(AuditLog.action == "download", AuditLog.user_id.in_(user_ids))
        .group_by(AuditLog.user_id)
        .all()
    )
    downloads_map = {uid: int(cnt) for uid, cnt in download_rows}

    comment_rows = (
        db.query(FileComment.user_id, func.count(FileComment.id))
        .filter(FileComment.user_id.in_(user_ids))
        .group_by(FileComment.user_id)
        .all()
    )
    comments_map = {uid: int(cnt) for uid, cnt in comment_rows}

    download_series_rows = (
        db.query(
            AuditLog.user_id,
            func.date(AuditLog.created_at),
            func.count(AuditLog.id),
        )
        .filter(
            AuditLog.action == "download",
            AuditLog.user_id.in_(user_ids),
            AuditLog.created_at >= datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc),
        )
        .group_by(AuditLog.user_id, func.date(AuditLog.created_at))
        .all()
    )
    download_series_map: dict[tuple, int] = {
        (uid, day.isoformat()): int(cnt) for uid, day, cnt in download_series_rows
    }

    comment_series_rows = (
        db.query(
            FileComment.user_id,
            func.date(FileComment.created_at),
            func.count(FileComment.id),
        )
        .filter(
            FileComment.user_id.in_(user_ids),
            FileComment.created_at >= datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc),
        )
        .group_by(FileComment.user_id, func.date(FileComment.created_at))
        .all()
    )
    comment_series_map: dict[tuple, int] = {
        (uid, day.isoformat()): int(cnt) for uid, day, cnt in comment_series_rows
    }

    out = []
    for u in users:
        out.append({
            "id": str(u.id),
            "email": u.email,
            "phone": u.phone,
            "is_active": u.is_active,
            "is_superuser": u.is_superuser,
            "last_login": last_login_map.get(u.id),
            "comments_count": comments_map.get(u.id, 0),
            "downloads_count": downloads_map.get(u.id, 0),
            "comments_series": [comment_series_map.get((u.id, d), 0) for d in day_strs],
            "downloads_series": [download_series_map.get((u.id, d), 0) for d in day_strs],
        })

    return {"days": day_strs, "users": out}


@router.patch("/users/{user_id}/active")
def set_user_active(
    user_id: str,
    payload: UserActiveUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный идентификатор пользователя")

    user = db.query(User).filter(User.id == user_uuid).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)

    return {"id": str(user.id), "is_active": user.is_active}
