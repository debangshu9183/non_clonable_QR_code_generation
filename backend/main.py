import uuid
import json
import base64
import io
from datetime import datetime
from typing import List

import qrcode
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, QRCode
from crypto_utils import sign_payload, verify_payload
from schemas import GenerateRequest, VerifyRequest, QRRecord

app = FastAPI(title="One-Time Secure QR System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_qr_image_b64(content: str) -> str:
    """Return a base64-encoded PNG of the QR code."""
    img = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    img.add_data(content)
    img.make(fit=True)
    pil_img = img.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/generate")
def generate_qr(req: GenerateRequest, db: Session = Depends(get_db)):
    """
    Generate a new one-time QR code.
    Optionally pass a 'label' to identify the QR (e.g. ticket number).
    Returns the signed QR data and a base64 PNG image.
    """
    qr_id = str(uuid.uuid4())

    # Persist
    db.add(QRCode(id=qr_id, label=req.label, used=False))
    db.commit()

    # Sign
    data = {"id": qr_id}
    payload, signature = sign_payload(data)
    qr_content = json.dumps({"payload": payload, "signature": signature})

    return {
        "qr_id":    qr_id,
        "label":    req.label,
        "qr_data":  qr_content,
        "qr_image": _make_qr_image_b64(qr_content),   # data URI ready
    }


@app.post("/verify")
def verify_qr(req: VerifyRequest, db: Session = Depends(get_db)):
    """
    Verify a QR code payload.
    - Checks cryptographic signature (tamper detection)
    - Checks one-time-use (replay detection)
    Marks the QR as used on first valid scan.
    """
    # 1. Signature check
    if not verify_payload(req.payload, req.signature):
        raise HTTPException(status_code=400, detail="Invalid QR — signature mismatch (tampered or forged)")

    # 2. Parse payload
    try:
        payload_data = json.loads(req.payload)
        qr_id = payload_data["id"]
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=400, detail="Malformed QR payload")

    # 3. Database lookup
    qr_entry = db.query(QRCode).filter(QRCode.id == qr_id).first()
    if not qr_entry:
        raise HTTPException(status_code=404, detail="QR not found — not issued by this system")

    # 4. One-time check
    if qr_entry.used:
        raise HTTPException(
            status_code=409,
            detail=f"QR already used at {qr_entry.used_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        )

    # 5. Mark used
    qr_entry.used    = True
    qr_entry.used_at = datetime.utcnow()
    db.commit()

    return {
        "status":  "valid",
        "qr_id":   qr_id,
        "label":   qr_entry.label,
        "message": "QR accepted and marked as used.",
    }


@app.get("/list", response_model=List[QRRecord])
def list_qrs(db: Session = Depends(get_db)):
    """Return all issued QR codes and their status."""
    return db.query(QRCode).order_by(QRCode.created_at.desc()).all()


@app.delete("/delete/{qr_id}")
def delete_qr(qr_id: str, db: Session = Depends(get_db)):
    """Delete a QR code record."""
    entry = db.query(QRCode).filter(QRCode.id == qr_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="QR not found")
    db.delete(entry)
    db.commit()
    return {"message": f"QR {qr_id} deleted."}


@app.get("/health")
def health():
    return {"status": "ok"}
