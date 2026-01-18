import uuid
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.database.get_db import get_db
from src.auth.dependencies import get_current_user
from src.database.models import FileLike, User, FilePage
from src.database.schemas import LikeIn, LikeOut
from src.services.description_service import get_file_or_404, ensure_file_access
from src.services.loging_service import write_audit

router = APIRouter(tags=["file_likes"])

@router.get("/files/{file_id}/like", response_model=LikeOut)
def get_my_file_like(
    request: Request,
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_file_or_404(db, file_id)

    like = (
        db.query(FileLike)
        .filter(FileLike.minio_object_id == file_id, FileLike.user_id == current_user.id)
        .one_or_none()
    )

    write_audit(
        db,
        request,
        current_user.id,
        action="file_like_get",
        entity="file_like",
        entity_id=str(file_id),
        meta={"my_like": like.is_like if like else None},
    )

    return LikeOut(my_like=like.is_like if like else None)

@router.post("/files/{file_id}/like", response_model=LikeOut)
def toggle_file_like(
    request: Request,
    file_id: uuid.UUID,
    payload: LikeIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_file_or_404(db, file_id)

    existing = (
        db.query(FileLike)
        .filter(FileLike.minio_object_id == file_id, FileLike.user_id == current_user.id)
        .one_or_none()
    )
    page = db.query(FilePage).filter(FilePage.minio_object_id == file_id).one_or_none()
    if not existing:
        db.add(FileLike(minio_object_id=file_id, user_id=current_user.id, is_like=payload.is_like))
        if payload.is_like and page:
            page.likes_count += 1
        db.commit()

        write_audit(
            db,
            request,
            current_user.id,
            action="file_like_set",
            entity="file_like",
            entity_id=str(file_id),
            meta={"is_like": payload.is_like, "mode": "create"},
        )
        return LikeOut(my_like=payload.is_like)

    # toggle (нажал то же самое)
    if existing.is_like == payload.is_like:
        db.delete(existing)
        if payload.is_like and page:
            page.likes_count = max(0, page.likes_count - 1)
        db.commit()

        write_audit(
            db,
            request,
            current_user.id,
            action="file_like_unset",
            entity="file_like",
            entity_id=str(file_id),
            meta={"is_like": payload.is_like, "mode": "delete"},
        )
        return LikeOut(my_like=None)

    if page:
        if (not existing.is_like) and payload.is_like:
            page.likes_count += 1
        elif existing.is_like and (not payload.is_like):
            page.likes_count = max(0, page.likes_count - 1)

    existing.is_like = payload.is_like
    db.commit()

    write_audit(
        db,
        request,
        current_user.id,
        action="file_like_set",
        entity="file_like",
        entity_id=str(file_id),
        meta={"is_like": payload.is_like, "mode": "update"},
    )
    return LikeOut(my_like=payload.is_like)