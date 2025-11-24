from fastapi import APIRouter, UploadFile, File
from src.services.minio_service import list_files, get_file_url, upload_file, delete_file

router = APIRouter(
    prefix="/files",
    tags=["files"]
)

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    return upload_file(file, file.filename)

@router.get("/")
async def list_all(page: int = 1, page_size: int = 10):
    return list_files(page, page_size)

@router.get("/download/{filename}")
async def download(filename: str):
    return {"url": get_file_url(filename)}

@router.delete("/delete/{filename}")
async def delete(filename: str):
    return delete_file(filename)

