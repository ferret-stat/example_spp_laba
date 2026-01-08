import uuid

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, UUID, Integer, BigInteger, UniqueConstraint
from sqlalchemy.orm import declarative_base, Mapped


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    email: Mapped[str] = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True
    )
    phone: Mapped[str] = Column(
        String(255),
        unique=True,
        nullable=True
    )
    hashed_password: Mapped[str] = Column(
        String(255),
        nullable=False
    )

    is_active: Mapped[bool] = Column(
        Boolean,
        default=True,
        nullable=False
    )
    is_superuser: Mapped[bool] = Column(
        Boolean,
        default=False,
        nullable=False
    )
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=False),
        default=datetime.now
    )

    def __repr__(self):
        return (
            f"<User(id={self.id}, email='{self.email}', "
            f"is_superuser={self.is_superuser})>"
        )
    
class MinioObject(Base):
    __tablename__ = "minio_objects"

    id = Column(UUID, primary_key=True)
    bucket = Column(String, nullable=False)
    object_name = Column(String, nullable=False)
    size = Column(BigInteger)
    etag = Column(String)
    last_modified = Column(DateTime)
    user_id = Column(UUID)
