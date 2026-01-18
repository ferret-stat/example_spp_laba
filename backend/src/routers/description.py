from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import uuid

from src.database.get_db import get_db
from src.database.models import FilePage
from src.auth.dependencies import get_current_user
from src.services.description_service import (get_minio_object_or_404, 
                                              ensure_owner_or_superuser)
from src.database.schemas import (FilePageCreate, 
                                  FilePageOut, 
                                  FilePageUpdate)
from src.services.loging_service import write_audit

router = APIRouter(prefix="/files", tags=["files"])

@router.get("/{file_id}/description", response_model=FilePageOut)
def get_file_page(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    page = db.query(FilePage).filter(FilePage.minio_object_id == file_id).one_or_none()

    if not page:
        return FilePageOut(minio_object_id=str(file_id), description=None, meta=None)

    return FilePageOut(
        minio_object_id=str(page.minio_object_id),
        description=page.description,
        meta=page.meta,
    )

@router.post("/{file_id}/description", response_model=FilePageOut, status_code=201)
def create_file_page(
    request: Request,
    file_id: uuid.UUID,
    payload: FilePageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    obj = get_minio_object_or_404(db, file_id)
    ensure_owner_or_superuser(current_user, obj)

    existing = db.query(FilePage).filter(FilePage.minio_object_id == file_id).one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Страница файла уже существует")

    page = FilePage(
        minio_object_id=file_id,
        description=payload.description,
        meta=payload.meta,
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    write_audit(
            db,
            request,
            current_user.id,
            action="file_like_set",
            entity="file_like",
            entity_id=str(file_id),
            meta={"is_like": payload.is_like, "mode": "create"},
        )

    return FilePageOut(
        minio_object_id=str(page.minio_object_id),
        description=page.description,
        meta=page.meta,
    )


@router.patch("/{file_id}/description", response_model=FilePageOut)
def update_file_page(
    request: Request,
    file_id: uuid.UUID,
    payload: FilePageUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    obj = get_minio_object_or_404(db, file_id)
    ensure_owner_or_superuser(current_user, obj)

    page = db.query(FilePage).filter(FilePage.minio_object_id == file_id).one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Страница файла не создана")

    if payload.description is not None:
        page.description = payload.description
    if payload.meta is not None:
        page.meta = payload.meta

    db.commit()
    db.refresh(page)
    write_audit(
            db,
            request,
            current_user.id,
            action="file_like_set",
            entity="file_like",
            entity_id=str(file_id),
            meta={"is_like": payload.is_like, "mode": "create"},
        )

    return FilePageOut(
        minio_object_id=str(page.minio_object_id),
        description=page.description,
        meta=page.meta,
    )

