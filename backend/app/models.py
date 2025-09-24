import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from geoalchemy2 import Geography

class Base(DeclarativeBase):
    pass

class Event(Base):
    __tablename__ = "events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    ts_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    ts_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    cls: Mapped[str] = mapped_column(String, index=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    feat_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    geom = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)

class Label(Base):
    __tablename__ = "labels"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default="now()")
