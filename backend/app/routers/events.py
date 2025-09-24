import json
import uuid
from typing import Optional, Tuple, List
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException, Request, Body
from sqlalchemy.orm import Session
from app.db import get_session
from app import crud
from app.schemas import EventOut, EventsOut, LabelIn, LabelOut

router = APIRouter()

def build_file_url(request: Request, stored_path: str) -> str:
    prefix = "/audio/"
    if stored_path.startswith(prefix):
        sub = stored_path[len(prefix):]
    else:
        sub = stored_path.lstrip("/")
    return str(request.url_for("audio", path=sub))

def to_out(request: Request, obj: any, latest_label: Optional[str] = None) -> EventOut:
    return EventOut(
        id=str(obj.id),
        node_id=obj.node_id,
        ts_start=obj.ts_start,
        ts_end=obj.ts_end,
        lat=obj.lat,
        lon=obj.lon,
        cls=obj.cls,
        confidence=obj.confidence,
        feat_json=obj.feat_json,
        file_url=build_file_url(request, obj.file_path),
        latest_label=latest_label,
    )

def parse_bbox(bbox: Optional[str]) -> Optional[Tuple[float, float, float, float]]:
    if not bbox:
        return None
    parts = bbox.split(",")
    if len(parts) != 4:
        raise HTTPException(status_code=422, detail="invalid_bbox")
    try:
        min_lon, min_lat, max_lon, max_lat = map(float, parts)
    except Exception:
        raise HTTPException(status_code=422, detail="invalid_bbox")
    return (min_lon, min_lat, max_lon, max_lat)

@router.post("/events", response_model=EventOut)
async def create_event(
    request: Request,
    node_id: str = Form(...),
    ts_start: datetime = Form(...),
    ts_end: datetime = Form(...),
    lat: float = Form(...),
    lon: float = Form(...),
    cls: str = Form(...),
    confidence: float = Form(...),
    feat_json: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
):
    data = await file.read()
    obj = crud.create_event(db, node_id, ts_start, ts_end, lat, lon, cls, confidence, feat_json, file.filename or "upload.bin", data)
    payload = to_out(request, obj, None)
    await request.app.state.manager.broadcast(json.dumps(payload.model_dump(mode="json")))
    return payload

@router.get("/events", response_model=EventsOut)
def get_events(
    request: Request,
    from_ts: Optional[datetime] = Query(None, alias="from"),
    to_ts: Optional[datetime] = Query(None, alias="to"),
    cls: Optional[str] = Query(None, alias="cls"),
    node_id: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
):
    bbox_tuple = parse_bbox(bbox)
    items = crud.list_events(db, from_ts, to_ts, cls, node_id, bbox_tuple, limit, offset)
    return {"items": [to_out(request, x, None) for x in items]}

@router.get("/events/{id}", response_model=EventOut)
def get_event_by_id(id: str, request: Request, db: Session = Depends(get_session)):
    obj = crud.get_event_by_id(db, id)
    if not obj:
        raise HTTPException(status_code=404, detail="not_found")
    latest = crud.get_latest_label_value(db, obj.id)
    return to_out(request, obj, latest)

@router.post("/events/{id}/label", response_model=EventOut)
def add_label(id: str, payload: LabelIn = Body(...), request: Request = None, db: Session = Depends(get_session)):
    if payload.source not in {"user", "system"}:
        raise HTTPException(status_code=422, detail="invalid_source")
    obj = crud.get_event_by_id(db, id)
    if not obj:
        raise HTTPException(status_code=404, detail="not_found")
    crud.create_label(db, obj.id, payload.label, payload.source)
    latest = crud.get_latest_label_value(db, obj.id)
    return to_out(request, obj, latest)

@router.get("/events/{id}/labels", response_model=List[LabelOut])
def list_labels(id: str, db: Session = Depends(get_session)):
    try:
        uid = uuid.UUID(id)
    except Exception:
        raise HTTPException(status_code=404, detail="not_found")
    labels = crud.list_labels_for_event(db, uid)
    return labels
