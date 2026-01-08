import uuid

from io import BytesIO
from minio import Minio

from src.utils.get_env import EnvConfig
from src.utils.pg_sync import sync_bucket
from src.database.models import MinioObject
from src.database.get_db import SessionLocal

client = Minio(
    EnvConfig.MINIO_ENDPOINT,
    access_key=EnvConfig.MINIO_ACCESS_KEY,
    secret_key=EnvConfig.MINIO_SECRET_KEY,
    secure=False
)

def list_files(page: int = 1, page_size: int = 10):
    objects = client.list_objects(EnvConfig.MINIO_BUCKET_NAME, recursive=True)
    files = [
        {
            "name": obj.object_name,
            "size": obj.size,
            "last_modified": obj.last_modified,
        }
        for obj in objects
    ]

    total = len(files)
    start = (page - 1) * page_size
    end = start + page_size
    sync_bucket(None)
    return {
        "files": files[start:end],
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size,
    }

def get_file_url(filename: str):
    return client.presigned_get_object(EnvConfig.MINIO_BUCKET_NAME, filename)


def upload_file(file, filename: str):
    file_bytes = file.file.read()
    file_size = len(file_bytes)
    if file_size == 0:
        raise ValueError("Файл пустой или не был передан")
    
    id = uuid.uuid4()
    obj = MinioObject(
        id=id,
        bucket=EnvConfig.MINIO_BUCKET_NAME,
        object_name=filename
    )
    with SessionLocal() as curr:
        curr.add(obj)
        curr.commit()

    client.put_object(
        bucket_name=EnvConfig.MINIO_BUCKET_NAME,
        object_name=str(id),
        data=BytesIO(file_bytes),
        length=file_size,
        content_type=file.content_type
    )
    sync_bucket(None)

    return {"message": "Файл загружен", "filename": filename}

def delete_file(filename: str):
    client.remove_object(EnvConfig.MINIO_BUCKET_NAME, filename)
    return {"message": f"Файл {filename} удалён"}

def get_file_url(filename: str):
    return client.presigned_get_object(EnvConfig.MINIO_BUCKET_NAME, filename)