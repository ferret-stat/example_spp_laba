import uuid

from io import BytesIO
from minio import Minio, S3Error
from sqlalchemy.orm import Session 

from src.utils.get_env import EnvConfig
from src.utils.pg_sync import sync_bucket
from src.database.models import MinioObject

client = Minio(
    EnvConfig.MINIO_ENDPOINT,
    access_key=EnvConfig.MINIO_ACCESS_KEY,
    secret_key=EnvConfig.MINIO_SECRET_KEY,
    secure=False
)

def list_files(
    session: Session,
    page: int = 1,
    page_size: int = 10,
):
    objects = client.list_objects(
        EnvConfig.MINIO_BUCKET_NAME,
        recursive=True
    )
    files = []
    ids = []
    for obj in objects:
        ids.append(uuid.UUID(obj.object_name))
        files.append({
            "id": obj.object_name,
            "size": obj.size,
            "last_modified": obj.last_modified,
        })
    db_objects = (
        session.query(MinioObject)
        .filter(MinioObject.id.in_(ids))
        .all()
    )

    names_map = {str(obj.id): obj.object_name for obj in db_objects}
    for f in files:
        f["object_name"] = names_map.get(f["id"])

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


def upload_file(session: Session, file, filename: str):
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
    session.add(obj)
    session.commit()
    client.put_object(
        bucket_name=EnvConfig.MINIO_BUCKET_NAME,
        object_name=str(id),
        data=BytesIO(file_bytes),
        length=file_size,
        content_type=file.content_type
    )
    sync_bucket(session, None)

    return {"message": "Файл загружен", "filename": filename}

def delete_file(filename: str):
    client.remove_object(EnvConfig.MINIO_BUCKET_NAME, filename)
    return {"message": f"Файл {filename} удалён"}

def get_file_url(filename: str):
    return client.presigned_get_object(EnvConfig.MINIO_BUCKET_NAME, filename)

def download_file(session: Session, file_id: str):
    file_uuid = uuid.UUID(file_id)
    db_object = (
        session.query(MinioObject)
        .filter(MinioObject.id == file_uuid)
        .one_or_none()
    )

    obj = client.get_object(
        EnvConfig.MINIO_BUCKET_NAME,
        file_id
    )

    return obj, db_object.object_name