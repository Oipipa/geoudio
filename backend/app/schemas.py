from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class EventOut(BaseModel):
    id: str
    node_id: str
    ts_start: datetime
    ts_end: datetime
    lat: float
    lon: float
    cls: str
    confidence: float
    feat_json: Optional[dict] = None
    file_url: str
    latest_label: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class EventsOut(BaseModel):
    items: List[EventOut]

class LabelIn(BaseModel):
    label: str
    source: str

class LabelOut(BaseModel):
    id: UUID
    event_id: UUID
    label: str
    source: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
