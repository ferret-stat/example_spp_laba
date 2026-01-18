from urllib.parse import quote
import uuid
from minio.error import S3Error
from sqlalchemy.orm import Session

from fastapi import (APIRouter, UploadFile, File, Depends,
                     HTTPException, Query, Request)
from fastapi.responses import StreamingResponse

from src.database.get_db import get_db
from src.database.models import User, MinioObjectTag
from src.auth.dependencies import get_current_user_id, get_current_user
from src.database.schemas import TagsUpdate
from src.services.description_service import (
    get_minio_object_or_404,
    ensure_owner_or_superuser,
)
from src.services.loging_service import write_audit
from src.services.minio_service import (list_files,
                                        download_file,
                                        upload_file,
                                        delete_file,
                                        delete_file_by_id,
                                        get_tags,
                                        attach_tags_to_object,
                                        user_files)

router = APIRouter(
    prefix="/files",
    tags=["files"]
)

@router.post("/upload")
async def upload(
    request: Request,
    user_id = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    tags: list[str] = Query(default=[]),
):
    return upload_file(user_id, db, file, file.filename, request, tags)

@router.get("/")
async def list_all(request: Request,
                   user_id = Depends(get_current_user_id), 
                   db: Session = Depends(get_db),
                   page: int = 1, 
                   page_size: int = 10, 
                   sort_by: str = "last_modified",
                   sort_dir: str = "desc",
                   tags: list[str] = Query(default=[]),):
    write_audit(db, request, user_id, "list",
                meta={"page": page, "page_size": page_size, "sort_by": sort_by,
                      "sort_dir": sort_dir, "tags": tags})
    return list_files(db, page, page_size, sort_by, sort_dir, tags)


@router.get("/my_books")
async def my_books(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "last_modified",
    sort_dir: str = "desc",
    tags: list[str] = Query(default=[]),
):
    write_audit(db, request, current_user.id, "my_books",
            meta={"page": page, "page_size": page_size, "sort_by": sort_by,
                    "sort_dir": sort_dir, "tags": tags})
    return user_files(db, current_user, page, page_size, sort_by, sort_dir, tags)


@router.get("/download/{filename}")
async def download(request: Request,
                   filename: str, 
                   db: Session = Depends(get_db),
                   user_id = Depends(get_current_user_id)):
    try:
        obj, obj_name = download_file(db, filename)
        write_audit(db, request, user_id, "download", entity_id=filename)
        filename_ascii = quote(obj_name)
        return StreamingResponse(
            obj,
            media_type="application/octet-stream",
            headers = {
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename_ascii}"
            }
        ) 
    except S3Error as e:
        write_audit(db, request, user_id, "download_error", entity_id=filename)
        raise HTTPException(status_code=404, detail="Файл не найден")

@router.get("/tags")
def list_tags(
    db: Session = Depends(get_db),
):
    return get_tags(db)


@router.put("/{file_id}/tags")
async def update_tags(
    request: Request,
    file_id: uuid.UUID,
    payload: TagsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = get_minio_object_or_404(db, file_id)
    ensure_owner_or_superuser(current_user, obj)

    db.query(MinioObjectTag).filter(
        MinioObjectTag.minio_object_id == file_id
    ).delete(synchronize_session=False)
    tags_norm = attach_tags_to_object(db, file_id, payload.tags)
    db.commit()

    write_audit(
        db,
        request,
        current_user.id,
        "update_tags",
        entity="minio_object",
        entity_id=str(file_id),
        meta={"tags": tags_norm},
    )

    return {"file_id": str(file_id), "tags": tags_norm}
    


@router.delete("/delete/{filename}")
async def delete(filename: str):
    return delete_file(filename)


@router.delete("/{file_id}")
async def delete_by_id(
    request: Request,
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = get_minio_object_or_404(db, file_id)
    ensure_owner_or_superuser(current_user, obj)
    try:
        deleted = delete_file_by_id(db, file_id)
    except S3Error:
        raise HTTPException(status_code=404, detail="Файл не найден")

    write_audit(
        db,
        request,
        current_user.id,
        "delete_file",
        entity="minio_object",
        entity_id=str(file_id),
        meta={"filename": deleted.object_name if deleted else None},
    )

    return {"message": "Файл удалён", "id": str(file_id)}

