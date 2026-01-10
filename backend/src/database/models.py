import uuid

from datetime import datetime
from sqlalchemy.orm import declarative_base, Mapped, relationship
from sqlalchemy import (Column, String, Boolean,
                        DateTime, UUID, Integer, 
                        BigInteger, UniqueConstraint, 
                        Index, ForeignKey)


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

    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bucket = Column(String, nullable=False)
    object_name = Column(String, nullable=False)
    size = Column(BigInteger)
    etag = Column(String)
    last_modified = Column(DateTime)

    user_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True))

    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary="minio_object_tags",
        back_populates="minio_objects",
        lazy="selectin",
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    created_at: Mapped[datetime] = Column(
        DateTime(timezone=False),
        default=datetime.now,
        nullable=False,
    )

    minio_objects: Mapped[list["MinioObject"]] = relationship(
        "MinioObject",
        secondary="minio_object_tags",
        back_populates="tags",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}')>"
    

class MinioObjectTag(Base):
    __tablename__ = "minio_object_tags"

    minio_object_id = Column(
        UUID(as_uuid=True),
        ForeignKey("minio_objects.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    created_at = Column(DateTime(timezone=False), default=datetime.now, nullable=False)

    __table_args__ = (
        UniqueConstraint("minio_object_id", "tag_id", name="uq_minio_object_tag"),
        Index("ix_minio_object_tags_tag_id", "tag_id"),
    )