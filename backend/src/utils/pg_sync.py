from minio import Minio
from sqlalchemy import text

from src.utils.get_env import EnvConfig
from src.database.get_db import SessionLocal

minio_client = Minio(
    EnvConfig.MINIO_ENDPOINT,
    access_key=EnvConfig.MINIO_ROOT_USER,
    secret_key=EnvConfig.MINIO_SECRET_KEY,
    secure=False
)

def sync_bucket(user_id):
    with SessionLocal() as cur:
        for obj in minio_client.list_objects(EnvConfig.MINIO_BUCKET_NAME, recursive=True):
            cur.execute(
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

            cur.commit()