import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.database.models import MinioObject, User, FileComment

def get_minio_object_or_404(db: Session, file_id: uuid.UUID) -> MinioObject:
    obj = db.query(MinioObject).filter(MinioObject.id == file_id).one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Файл не найден")
    return obj

def ensure_owner_or_superuser(current_user: User, obj: MinioObject):
    if current_user.is_superuser:
        return
    if not obj.user_id or obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
def ensure_file_access(current_user, obj):
    if current_user.is_superuser:
        return
    if not obj.user_id or obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к файлу")

def ensure_comment_edit_rights(current_user, file_obj, comment):
    if current_user.is_superuser:
        return
    if comment.user_id == current_user.id:
        return
    if file_obj.user_id == current_user.id:
        return
    raise HTTPException(status_code=403, detail="Нет прав на изменение комментария")

def get_file_or_404(db: Session, file_id: uuid.UUID) -> MinioObject:
    obj = db.query(MinioObject).filter(MinioObject.id == file_id).one_or_none()
    if not obj:
        raise HTTPException(404, "Файл не найден")
    return obj

def get_comment_or_404(db: Session, comment_id: uuid.UUID) -> FileComment:
    c = db.query(FileComment).filter(FileComment.id == comment_id).one_or_none()
    if not c:
        raise HTTPException(404, "Комментарий не найден")
    return c

def ensure_file_access(current_user: User, obj: MinioObject):
    if current_user.is_superuser:
        return
    if not obj.user_id or obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к файлу")