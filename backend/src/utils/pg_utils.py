import os
import uuid
from datetime import datetime, timezone
from minio import Minio
from sqlalchemy import text

from src.utils.get_env import EnvConfig
from sqlalchemy.exc import IntegrityError
from src.database.models import Tag, MinioObjectTag

minio_client = Minio(
    EnvConfig.MINIO_ENDPOINT,
    access_key=EnvConfig.MINIO_ROOT_USER,
    secret_key=EnvConfig.MINIO_SECRET_KEY,
    secure=False
)

def sync_bucket(session, user_id):
    for obj in minio_client.list_objects(EnvConfig.MINIO_BUCKET_NAME, recursive=True):
        session.execute(
            text("""
                    UPDATE minio_objects
                    SET
                        size = :size,
                        etag = :etag,
                        last_modified = :last_modified
                    WHERE id = :id
            """),
            {
                "id": obj.object_name,
                "size": obj.size,
                "etag": obj.etag,
                "last_modified": obj.last_modified,
            }
        )
        session.commit()

def text_to_uuid(text: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, text)

def get_format(filename):
    return os.path.splitext(filename)[1].lstrip('.').lower()

def load_format_tag(session, filename):
    name = get_format(filename)
    if not name:
        return None
    tag_id = text_to_uuid(name)
    tag = session.query(Tag).filter_by(id=tag_id).first()
    if tag:
        return tag
    tag = Tag(
        id=tag_id,
        name=name,
        created_at=datetime.now(timezone.utc)
    )
    try:
        session.add(tag)
        session.commit()
        return tag
    except IntegrityError:
        session.rollback()
        return (session.query(Tag)
                .filter_by(id=id)
                .one())

def load_object_tags(session, minio_object_id, tag_id):
    object_tag = MinioObjectTag(
        minio_object_id=minio_object_id,
        tag_id=tag_id,
        created_at=datetime.now(timezone.utc)
    )

    try:
        session.add(object_tag)
        session.commit()
        return object_tag
    except IntegrityError:
        session.rollback()
        return (session.query(MinioObjectTag)
                .filter_by(minio_object_id=minio_object_id, tag_id=tag_id)
                .one())