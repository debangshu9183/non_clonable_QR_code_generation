from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GenerateRequest(BaseModel):
    label: Optional[str] = None   # e.g. "Ticket #42" or "Invoice INV-001"


class VerifyRequest(BaseModel):
    payload:   str
    signature: str


class QRRecord(BaseModel):
    id:         str
    label:      Optional[str]
    used:       bool
    created_at: datetime
    used_at:    Optional[datetime]

    class Config:
        from_attributes = True
