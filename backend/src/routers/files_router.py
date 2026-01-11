from urllib.parse import quote
from minio.error import S3Error
from sqlalchemy.orm import Session

from fastapi import (APIRouter, UploadFile, File, Depends,
                     HTTPException, Query, Request)
from fastapi.responses import StreamingResponse

from src.database.get_db import get_db
from src.auth.dependencies import get_current_user_id
from src.services.loging_service import write_audit
from src.services.minio_service import list_files, download_file, upload_file, delete_file, get_tags

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
    


@router.delete("/delete/{filename}")
async def delete(filename: str):
    return delete_file(filename)

