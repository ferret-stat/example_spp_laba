from minio.error import S3Error
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from src.database.get_db import get_db
from src.services.minio_service import list_files, download_file, upload_file, delete_file, get_tags

router = APIRouter(
    prefix="/files",
    tags=["files"]
)

@router.post("/upload")
async def upload(db: Session = Depends(get_db), file: UploadFile = File(...)):
    return upload_file(db, file, file.filename)

@router.get("/")
async def list_all(db: Session = Depends(get_db),
                   page: int = 1, 
                   page_size: int = 10, 
                   sort_by: str = "last_modified",
                   sort_dir: str = "desc",
                   tags: list[str] = Query(default=[]),):
    return list_files(db, page, page_size, sort_by, sort_dir, tags)

@router.get("/download/{filename}")
async def download(filename: str, db: Session = Depends(get_db)):
    try:
        obj, obj_name = download_file(db, filename)
        return StreamingResponse(
            obj,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{obj_name}"'
            }
        ) 
    except S3Error as e:
        raise HTTPException(status_code=404, detail="Файл не найден")

@router.get("/tags")
def list_tags(
    db: Session = Depends(get_db),
):
    return get_tags(db)
    


@router.delete("/delete/{filename}")
async def delete(filename: str):
    return delete_file(filename)

