import os
import uuid
import json
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, cast
from app.config import settings
from app.models import Event, Label
from geoalchemy2 import Geometry

def save_file_and_build_path(ts: datetime, filename: str) -> tuple[str, str]:
    root = settings.storage_root
    y = f"{ts.year:04d}"
    m = f"{ts.month:02d}"
    d = f"{ts.day:02d}"
    ext = ""
    if "." in filename:
        ext = "." + filename.split(".")[-1].lower()
    if ext == "":
        ext = ".bin"
    uid = str(uuid.uuid4())
    rel = f"/audio/{y}/{m}/{d}/{uid}{ext}"
    abs_dir = os.path.join(root, "audio", y, m, d)
    os.makedirs(abs_dir, exist_ok=True)
    abs_path = os.path.join(abs_dir, f"{uid}{ext}")
    return rel, abs_path

def create_event(db: Session, node_id: str, ts_start: datetime, ts_end: datetime, lat: float, lon: float, cls: str, confidence: float, feat_json_str: Optional[str], upload_filename: str, file_bytes: bytes):
    rel_path, abs_path = save_file_and_build_path(ts_start, upload_filename)
    with open(abs_path, "wb") as f:
        f.write(file_bytes)
    payload = None
    if feat_json_str:
        payload = json.loads(feat_json_str)
    obj = Event(
        node_id=node_id,
        ts_start=ts_start,
        ts_end=ts_end,
        lat=lat,
        lon=lon,
        cls=cls,
        confidence=confidence,
        feat_json=payload,
        file_path=rel_path,
        geom=func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def list_events(db: Session, from_ts: Optional[datetime], to_ts: Optional[datetime], cls: Optional[str], node_id: Optional[str], bbox: Optional[Tuple[float, float, float, float]], limit: int, offset: int) -> List[Event]:
    conds = []
    if from_ts:
        conds.append(Event.ts_start >= from_ts)
    if to_ts:
        conds.append(Event.ts_end <= to_ts)
    if cls:
        conds.append(Event.cls == cls)
    if node_id:
        conds.append(Event.node_id == node_id)
    if bbox:
        min_lon, min_lat, max_lon, max_lat = bbox
        env = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        conds.append(func.ST_Intersects(cast(Event.geom, Geometry(geometry_type="POINT", srid=4326)), env))
    stmt = select(Event).order_by(Event.ts_start.desc()).offset(offset).limit(limit)
    if conds:
        stmt = stmt.where(and_(*conds))
    return list(db.execute(stmt).scalars().all())

def get_event_by_id(db: Session, id_str: str) -> Optional[Event]:
    try:
        uid = uuid.UUID(id_str)
    except Exception:
        return None
    stmt = select(Event).where(Event.id == uid)
    return db.execute(stmt).scalars().first()

def create_label(db: Session, event_id: uuid.UUID, label: str, source: str) -> "Label":
    obj = Label(event_id=event_id, label=label, source=source)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def list_labels_for_event(db: Session, event_id: uuid.UUID) -> List["Label"]:
    stmt = select(Label).where(Label.event_id == event_id).order_by(Label.created_at.asc(), Label.id.asc())
    return list(db.execute(stmt).scalars().all())

def get_latest_label_value(db: Session, event_id: uuid.UUID) -> Optional[str]:
    stmt = select(Label.label).where(Label.event_id == event_id).order_by(Label.created_at.desc(), Label.id.desc()).limit(1)
    row = db.execute(stmt).first()
    if not row:
        return None
    return row[0]
