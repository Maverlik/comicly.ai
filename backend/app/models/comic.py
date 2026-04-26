from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Comic(Base):
    __tablename__ = "comics"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    style_preset: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ComicScene(Base):
    __tablename__ = "comic_scenes"
    __table_args__ = (
        UniqueConstraint("id", "comic_id", name="uq_comic_scenes_id_comic_id"),
        UniqueConstraint("comic_id", "position", name="uq_comic_scenes_comic_position"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    comic_id: Mapped[UUID] = mapped_column(
        ForeignKey("comics.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    script_text: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ComicPage(Base):
    __tablename__ = "comic_pages"
    __table_args__ = (
        ForeignKeyConstraint(
            ["comic_id", "scene_id"],
            ["comic_scenes.comic_id", "comic_scenes.id"],
            name="fk_comic_pages_scene_same_comic",
        ),
        UniqueConstraint("comic_id", "page_number", name="uq_comic_pages_comic_page"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    comic_id: Mapped[UUID] = mapped_column(
        ForeignKey("comics.id", ondelete="CASCADE"),
        nullable=False,
    )
    scene_id: Mapped[UUID | None]
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(2048))
    storage_key: Mapped[str | None] = mapped_column(String(1024))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
