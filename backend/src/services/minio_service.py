import uuid

from io import BytesIO
from minio import Minio
from typing import Iterable
from sqlalchemy import select, func
from sqlalchemy.orm import Session 

from src.services.loging_service import write_audit
from src.utils.get_env import EnvConfig
from src.utils.pg_utils import (sync_bucket, 
                                load_format_tag, 
                                text_to_uuid, 
                                get_format, 
                                load_object_tags)
from src.database.models import (MinioObject,
                                 MinioObjectTag,
                                 Tag,
                                 User,
                                 FileLike,
                                 FileComment)

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
    obj_map = {str(o.id): o for o in db_objects}
    user_ids = {o.user_id for o in db_objects if o.user_id}
    users_map: dict[uuid.UUID, str] = {}
    if user_ids:
        users = (
            session.query(User.id, User.email, User.phone)
            .filter(User.id.in_(user_ids))
            .all()
        )

        for uid, email, phone in users:
            users_map[uid] = email or phone
    

    tag_rows = (
        session.query(MinioObjectTag.minio_object_id, Tag.name)
        .join(Tag, Tag.id == MinioObjectTag.tag_id)
        .filter(MinioObjectTag.minio_object_id.in_(ids))
        .all()
    )

    tags_map: dict[str, list[str]] = {}
    for obj_id, tag_name in tag_rows:
        tags_map.setdefault(str(obj_id), []).append(tag_name)

    comment_rows = (
        session.query(FileComment.minio_object_id, func.count(FileComment.id))
        .filter(
            FileComment.minio_object_id.in_(ids),
            FileComment.is_deleted.is_(False),
        )
        .group_by(FileComment.minio_object_id)
        .all()
    )
    comments_map = {str(obj_id): int(count) for obj_id, count in comment_rows}

    like_rows = (
        session.query(FileLike.minio_object_id, func.count(FileLike.id))
        .filter(FileLike.is_like.is_(True), FileLike.minio_object_id.in_(ids))
        .group_by(FileLike.minio_object_id)
        .all()
    )
    likes_map = {str(obj_id): int(count) for obj_id, count in like_rows}

    for f in files:
        o = obj_map.get(f["id"])

        f["object_name"] = o.object_name if o else None
        f["tags"] = tags_map.get(f["id"], [])
        f["likes_count"] = likes_map.get(f["id"], 0)
        f["comments_count"] = comments_map.get(f["id"], 0)

        if o and o.user_id:
            f["author"] = users_map.get(o.user_id)
        else:
            f["author"] = None

    # Сортировка
    allowed = {"size", "object_name", "last_modified", "likes_count"}
    if sort_by not in allowed:
        sort_by = "last_modified"

    reverse = (sort_dir.lower() == "desc")

    def sort_key(item):
        v = item.get(sort_by)
        if sort_by == "object_name":
            return (v is None, (v or "").lower())
        if sort_by == "likes_count":
            return (v is None, int(v or 0))
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

def user_files(
    session: Session,
    current_user: User,                
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "last_modified",
    sort_dir: str = "desc",
    tags: Iterable[str] | None = None,
):
    tags = normalize_tags(tags)
    q = session.query(MinioObject)
    if not current_user.is_superuser:
        q = q.filter(MinioObject.user_id == current_user.id)
    if tags:
        q = (
            q.join(MinioObjectTag, MinioObjectTag.minio_object_id == MinioObject.id)
             .join(Tag, Tag.id == MinioObjectTag.tag_id)
             .filter(Tag.name.in_(tags))
             .distinct()
        )
    db_objects = q.all()

    if not db_objects:
        return {"files": [], "total": 0, "page": page, "pages": 0}

    obj_map = {str(o.id): o for o in db_objects}
    ids = [o.id for o in db_objects]
    user_ids = {o.user_id for o in db_objects if o.user_id}
    users_map: dict[uuid.UUID, str] = {}
    if user_ids:
        users = (
            session.query(User.id, User.email, User.phone)
            .filter(User.id.in_(user_ids))
            .all()
        )
        for uid, email, phone in users:
            users_map[uid] = email or phone
    tag_rows = (
        session.query(MinioObjectTag.minio_object_id, Tag.name)
        .join(Tag, Tag.id == MinioObjectTag.tag_id)
        .filter(MinioObjectTag.minio_object_id.in_(ids))
        .all()
    )
    tags_map: dict[str, list[str]] = {}
    for obj_id, tag_name in tag_rows:
        tags_map.setdefault(str(obj_id), []).append(tag_name)
    comment_rows = (
        session.query(FileComment.minio_object_id, func.count(FileComment.id))
        .filter(
            FileComment.minio_object_id.in_(ids),
            FileComment.is_deleted.is_(False),
        )
        .group_by(FileComment.minio_object_id)
        .all()
    )
    comments_map = {str(obj_id): int(count) for obj_id, count in comment_rows}
    like_rows = (
        session.query(FileLike.minio_object_id, func.count(FileLike.id))
        .filter(FileLike.is_like.is_(True), FileLike.minio_object_id.in_(ids))
        .group_by(FileLike.minio_object_id)
        .all()
    )
    likes_map = {str(obj_id): int(count) for obj_id, count in like_rows}
    minio_meta: dict[str, dict] = {}
    for obj in client.list_objects(EnvConfig.MINIO_BUCKET_NAME, recursive=True):
        try:
            obj_id = str(uuid.UUID(obj.object_name))
        except Exception:
            continue
        if obj_id in obj_map:
            minio_meta[obj_id] = {"size": obj.size, "last_modified": obj.last_modified}
    files = []
    for oid_str, o in obj_map.items():
        m = minio_meta.get(oid_str, {})
        files.append({
            "id": oid_str,
            "object_name": o.object_name,
            "size": m.get("size"),
            "last_modified": m.get("last_modified"),
            "tags": tags_map.get(oid_str, []),
            "likes_count": likes_map.get(oid_str, 0),
            "comments_count": comments_map.get(oid_str, 0),
            "author": users_map.get(o.user_id) if o.user_id else None,
        })
    allowed = {"size", "object_name", "last_modified", "author", "likes_count"}
    if sort_by not in allowed:
        sort_by = "last_modified"

    reverse = (sort_dir.lower() == "desc")
    def sort_key(item):
        v = item.get(sort_by)
        if sort_by in ("object_name", "author"):
            return (v is None, (v or "").lower())
        if sort_by == "likes_count":
            return (v is None, int(v or 0))
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


def delete_file_by_id(session: Session, file_id: uuid.UUID):
    obj = (
        session.query(MinioObject)
        .filter(MinioObject.id == file_id)
        .one_or_none()
    )
    if not obj:
        return None

    client.remove_object(EnvConfig.MINIO_BUCKET_NAME, str(file_id))
    session.delete(obj)
    session.commit()
    return obj

def get_file_url(filename: str):
    return client.presigned_get_object(EnvConfig.MINIO_BUCKET_NAME, filename)

def attach_tags_to_object(session: Session, obj_id: uuid.UUID, tags: list[str]) -> list[str]:
    tags = normalize_tags(tags)
    if not tags:
        return []
    existing = session.execute(
        select(Tag).where(Tag.name.in_(tags))
    ).scalars().all()
    existing_map = {t.name: t for t in existing}

    missing = [name for name in tags if name not in existing_map]
    if missing:
        session.add_all([Tag(name=name) for name in missing])
        session.flush()
        new_tags = session.execute(
            select(Tag).where(Tag.name.in_(missing))
        ).scalars().all()
        for t in new_tags:
            existing_map[t.name] = t
    for name in tags:
        tag_id = existing_map[name].id
        session.merge(MinioObjectTag(minio_object_id=obj_id, tag_id=tag_id))

    return tags

def normalize_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    out = []
    seen = set()
    for t in tags:
        if not t:
            continue
        name = t.strip().lower()
        if not name:
            continue
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out

def upload_file(user_id, session: Session, file, filename: str, request, tags: list[str] | None = None):
    file_bytes = file.file.read()
    file_size = len(file_bytes)
    if file_size == 0:
        raise ValueError("Файл пустой или не был передан")
    obj_id = uuid.uuid4()

    obj = MinioObject(
        id=obj_id,
        bucket=EnvConfig.MINIO_BUCKET_NAME,
        object_name=filename,
        user_id=user_id
    )
    session.add(obj)
    session.flush()
    tags_norm = attach_tags_to_object(session, obj_id, tags or [])
    load_format_tag(session, filename)
    load_object_tags(session, obj_id, text_to_uuid(get_format(filename)))
    write_audit(
        session,
        request,
        user_id,
        "upload",
        entity_id=str(obj_id),
        meta={"content_type": file.content_type, "tags": tags_norm}
    )

    session.commit()

    client.put_object(
        bucket_name=EnvConfig.MINIO_BUCKET_NAME,
        object_name=str(obj_id),
        data=BytesIO(file_bytes),
        length=file_size,
        content_type=file.content_type
    )

    sync_bucket(session, None)

    return {"message": "Файл загружен", "id": str(obj_id), "filename": filename, "tags": tags_norm}

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
