import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from src.database.get_db import get_db
from src.auth.dependencies import get_current_user
from src.database.models import (
    FileComment,
    CommentLike,
    User,
)
from src.database.schemas import (
    CommentOut,
    CommentCreate,
    CommentUpdate,
    LikeOut,
    LikeIn,
)
from src.services.description_service import (
    get_file_or_404,
    get_comment_or_404,
    ensure_comment_edit_rights,
)

from src.services.loging_service import write_audit

router = APIRouter(tags=["comments"])


@router.get("/files/{file_id}/comments", response_model=list[CommentOut])
def list_comments(
    request: Request,
    file_id: uuid.UUID,
    tree: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_file_or_404(db, file_id)

    write_audit(
        db,
        request,
        current_user.id,
        action="comments_list",
        entity="comment",
        entity_id=str(file_id),
        meta={"tree": tree, "limit": limit, "offset": offset},
    )

    q = db.query(FileComment).filter(FileComment.minio_object_id == file_id)
    q = q.order_by(FileComment.created_at.desc()).offset(offset).limit(limit)
    comments = q.all()

    user_ids = {c.user_id for c in comments if c.user_id}
    users_map = {}
    if user_ids:
        rows = db.query(User.id, User.email, User.phone).filter(User.id.in_(user_ids)).all()
        for uid, email, phone in rows:
            users_map[uid] = email or phone

    out = []
    for c in comments:
        out.append(CommentOut(
            id=str(c.id),
            file_id=str(c.minio_object_id),
            user_id=str(c.user_id) if c.user_id else None,
            author=users_map.get(c.user_id) if c.user_id else None,
            parent_id=str(c.parent_id) if c.parent_id else None,
            body="[удалено]" if c.is_deleted else c.body,
            is_deleted=c.is_deleted,
            likes_count=c.likes_count,
            created_at=c.created_at,
            updated_at=c.updated_at,
        ))

    return out


@router.post("/files/{file_id}/comments", response_model=CommentOut, status_code=201)
def create_comment(
    request: Request,
    file_id: uuid.UUID,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = get_file_or_404(db, file_id)
    parent_uuid = payload.parent_id

    if parent_uuid:
        parent = (
            db.query(FileComment)
            .filter(FileComment.id == parent_uuid, FileComment.minio_object_id == file_id)
            .one_or_none()
        )
        if not parent:
            write_audit(
                db,
                request,
                current_user.id,
                action="comment_create_error",
                entity="comment",
                entity_id=str(file_id),
                meta={"reason": "bad_parent_id", "parent_id": str(parent_uuid)},
            )
            raise HTTPException(400, "parent_id неверный (не найден или не от этого файла)")

    c = FileComment(
        minio_object_id=file_id,
        user_id=current_user.id,
        parent_id=parent_uuid,
        body=payload.body,
        is_deleted=False,
        likes_count=0,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    write_audit(
        db,
        request,
        current_user.id,
        action="comment_create",
        entity="comment",
        entity_id=str(c.id),
        meta={"file_id": str(file_id), "parent_id": str(parent_uuid) if parent_uuid else None},
    )

    author = current_user.email or current_user.phone

    return CommentOut(
        id=str(c.id),
        file_id=str(c.minio_object_id),
        user_id=str(c.user_id),
        author=author,
        parent_id=str(c.parent_id) if c.parent_id else None,
        body=c.body,
        is_deleted=c.is_deleted,
        likes_count=c.likes_count,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.patch("/comments/{comment_id}", response_model=CommentOut)
def update_comment(
    request: Request,
    comment_id: uuid.UUID,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = get_comment_or_404(db, comment_id)
    obj = get_file_or_404(db, c.minio_object_id)

    ensure_comment_edit_rights(current_user, obj, c)

    if c.is_deleted:
        write_audit(
            db,
            request,
            current_user.id,
            action="comment_update_error",
            entity="comment",
            entity_id=str(comment_id),
            meta={"reason": "comment_deleted"},
        )
        raise HTTPException(409, "Нельзя редактировать удалённый комментарий")

    old_body = c.body
    c.body = payload.body
    db.commit()
    db.refresh(c)
    write_audit(
        db,
        request,
        current_user.id,
        action="comment_update",
        entity="comment",
        entity_id=str(c.id),
        meta={"file_id": str(c.minio_object_id), "changed": old_body != c.body},
    )

    author = None
    if c.user_id:
        u = db.query(User).filter(User.id == c.user_id).one_or_none()
        author = (u.email or u.phone) if u else None

    return CommentOut(
        id=str(c.id),
        file_id=str(c.minio_object_id),
        user_id=str(c.user_id) if c.user_id else None,
        author=author,
        parent_id=str(c.parent_id) if c.parent_id else None,
        body=c.body,
        is_deleted=c.is_deleted,
        likes_count=c.likes_count,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    request: Request,
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = get_comment_or_404(db, comment_id)
    obj = get_file_or_404(db, c.minio_object_id)

    ensure_comment_edit_rights(current_user, obj, c)
    c.is_deleted = True
    c.body = "[удалено]"
    db.commit()

    write_audit(
        db,
        request,
        current_user.id,
        action="comment_delete",
        entity="comment",
        entity_id=str(comment_id),
        meta={"file_id": str(c.minio_object_id)},
    )
    return


@router.get("/comments/{comment_id}/like", response_model=LikeOut)
def get_my_comment_like(
    request: Request,
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = get_comment_or_404(db, comment_id)
    get_file_or_404(db, c.minio_object_id)

    like = (
        db.query(CommentLike)
        .filter(CommentLike.comment_id == comment_id, CommentLike.user_id == current_user.id)
        .one_or_none()
    )
    write_audit(
        db,
        request,
        current_user.id,
        action="comment_like_get",
        entity="comment_like",
        entity_id=str(comment_id),
        meta={"my_like": like.is_like if like else None},
    )

    return LikeOut(my_like=like.is_like if like else None)


@router.post("/comments/{comment_id}/like", response_model=LikeOut)
def toggle_comment_like(
    request: Request,
    comment_id: uuid.UUID,
    payload: LikeIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = get_comment_or_404(db, comment_id)
    get_file_or_404(db, c.minio_object_id)

    existing = (
        db.query(CommentLike)
        .filter(CommentLike.comment_id == comment_id, CommentLike.user_id == current_user.id)
        .one_or_none()
    )

    # ставим впервые
    if not existing:
        db.add(CommentLike(comment_id=comment_id, user_id=current_user.id, is_like=payload.is_like))
        if payload.is_like:
            c.likes_count += 1
        db.commit()

        write_audit(
            db,
            request,
            current_user.id,
            action="comment_like_set",
            entity="comment_like",
            entity_id=str(comment_id),
            meta={"is_like": payload.is_like, "mode": "create"},
        )
        return LikeOut(my_like=payload.is_like)

    if existing.is_like == payload.is_like:
        db.delete(existing)
        if payload.is_like:
            c.likes_count = max(0, c.likes_count - 1)
        db.commit()

        write_audit(
            db,
            request,
            current_user.id,
            action="comment_like_unset",
            entity="comment_like",
            entity_id=str(comment_id),
            meta={"is_like": payload.is_like, "mode": "delete"},
        )
        return LikeOut(my_like=None)

    # смена like/dislike
    if existing.is_like and not payload.is_like:
        c.likes_count = max(0, c.likes_count - 1)
    elif (not existing.is_like) and payload.is_like:
        c.likes_count += 1

    existing.is_like = payload.is_like
    db.commit()

    write_audit(
        db,
        request,
        current_user.id,
        action="comment_like_set",
        entity="comment_like",
        entity_id=str(comment_id),
        meta={"is_like": payload.is_like, "mode": "update"},
    )
    return LikeOut(my_like=payload.is_like)
