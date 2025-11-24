from io import BytesIO
from minio import Minio
from src.utils.get_env import EnvConfig

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

    client.put_object(
        bucket_name=EnvConfig.MINIO_BUCKET_NAME,
        object_name=filename,
        data=BytesIO(file_bytes),
        length=file_size,
        content_type=file.content_type
    )

    return {"message": "Файл загружен", "filename": filename}

def delete_file(filename: str):
    client.remove_object(EnvConfig.MINIO_BUCKET_NAME, filename)
    return {"message": f"Файл {filename} удалён"}

def get_file_url(filename: str):
    return client.presigned_get_object(EnvConfig.MINIO_BUCKET_NAME, filename)