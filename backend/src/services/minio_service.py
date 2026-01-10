import uuid

from io import BytesIO
from minio import Minio, S3Error
from typing import Iterable
from sqlalchemy import func
from sqlalchemy.orm import Session 

from src.utils.get_env import EnvConfig
from src.utils.pg_utils import sync_bucket, load_format_tag, text_to_uuid, get_format, load_object_tags
from src.database.models import MinioObject, MinioObjectTag, Tag

client = Minio(
    EnvConfig.MINIO_ENDPOINT,
    access_key=EnvConfig.MINIO_ACCESS_KEY,
    secret_key=EnvConfig.MINIO_SECRET_KEY,
    secure=False
)

def normalize_tags(tags):
    if not tags:
        return []
    if isinstance(tags, str):
        return [tags.strip().lower()] if tags.strip() else []
    return [t.strip().lower() for t in tags if t and t.strip()]

def list_files(
    session: Session,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "last_modified",   # "size", "object_name", "last_modified"
    sort_dir: str = "desc",           # "asc", "desc",
    tags: Iterable[str] | None = None, 
):
    objects = client.list_objects(
        EnvConfig.MINIO_BUCKET_NAME,
        recursive=True
    )
    # tags = [t.strip().lower() for t in (tags or []) if t and t.strip()]
    tags = normalize_tags(tags)
    print(tags)
    files = []
    ids = []
    for obj in objects:
        obj_id = uuid.UUID(obj.object_name)
        ids.append(obj_id)
        files.append({
            "id": str(obj_id),
            "size": obj.size,
            "last_modified": obj.last_modified,
        })

    if not ids:
        return {"files": [], "total": 0, "page": page, "pages": 0}
    
    if tags:
        tag_ids = (
            session.query(Tag.id)
            .filter(Tag.name.in_(tags))
            .subquery()
        )

        filtered_ids = (
            session.query(MinioObjectTag.minio_object_id)
            .filter(MinioObjectTag.tag_id.in_(tag_ids))
            .distinct()
            .all()
        )

        allowed_ids = {row[0] for row in filtered_ids}
        ids = [i for i in ids if i in allowed_ids]
        files = [f for f in files if uuid.UUID(f["id"]) in allowed_ids]
        print(files)

        if not ids:
            return {"files": [], "total": 0, "page": page, "pages": 0}

    db_objects = (
        session.query(MinioObject)
        .filter(MinioObject.id.in_(ids))
        .all()
    )
    names_map = {str(o.id): o.object_name for o in db_objects}

    tag_rows = (
        session.query(MinioObjectTag.minio_object_id, Tag.name)
        .join(Tag, Tag.id == MinioObjectTag.tag_id)
        .filter(MinioObjectTag.minio_object_id.in_(ids))
        .all()
    )

    tags_map: dict[str, list[str]] = {}
    for obj_id, tag_name in tag_rows:
        tags_map.setdefault(str(obj_id), []).append(tag_name)

    for f in files:
        f["object_name"] = names_map.get(f["id"])
        f["tags"] = tags_map.get(f["id"], [])

    # Сортировка
    allowed = {"size", "object_name", "last_modified"}
    if sort_by not in allowed:
        sort_by = "last_modified"

    reverse = (sort_dir.lower() == "desc")

    def sort_key(item):
        v = item.get(sort_by)
        if sort_by == "object_name":
            return (v is None, (v or "").lower())
        return (v is None, v)

    files.sort(key=sort_key, reverse=reverse)

    total = len(files)
    start = max(0, (page - 1) * page_size)
    end = start + page_size

    return {
        "files": files[start:end],
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size,
        "sort": {"by": sort_by, "dir": "desc" if reverse else "asc"},
    }

def get_tags(session):
    tags = (
        session.query(Tag)
        .order_by(Tag.name.asc())
        .all()
    )

    return [
        {
            "id": str(tag.id),
            "name": tag.name,
            "created_at": tag.created_at,
        }
        for tag in tags
    ]

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
    load_format_tag(session, filename)
    load_object_tags(session, id, text_to_uuid(get_format(filename)))

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