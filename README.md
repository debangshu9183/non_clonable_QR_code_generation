# One-Time Secure QR System

A cryptographically signed, one-time-use QR code system built with FastAPI + SQLite (backend) and plain HTML/JS (frontend).

---

## How it works

1. **Generate** — server creates a UUID, signs it with an RSA private key, encodes it as a QR code
2. **Scan / Verify** — scanner sends the payload + signature to the server
3. **Check** — server verifies the signature (tamper detection) and the one-time-use flag (replay detection)
4. **Mark** — on first valid scan, the QR is marked as used and can never be accepted again

---

## Security properties

| Threat              | Protection                                      |
|---------------------|-------------------------------------------------|
| Tampered QR         | RSA-PSS SHA-256 signature verification          |
| Forged QR           | Signature invalid without the server's key      |
| Replay / reuse      | `used` flag set in DB on first scan             |
| Key loss on restart | Private key persisted to `private_key.pem`      |

---

## Project structure

```
secure-qr-system/
├── backend/
│   ├── main.py           # FastAPI app, all routes
│   ├── database.py       # SQLAlchemy models + get_db
│   ├── crypto_utils.py   # RSA sign / verify (persistent key)
│   ├── schemas.py        # Pydantic models
│   └── requirements.txt
└── frontend/
    └── index.html        # Single-file UI (Generate / Scan / List)
```

---

## Setup

### 1. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the server

```bash
uvicorn main:app --reload
```

API will be at: http://127.0.0.1:8000  
Swagger docs:  http://127.0.0.1:8000/docs

### 3. Open the frontend

Just open `frontend/index.html` in your browser — no build step needed.

> If you get CORS errors, make sure the backend is running on port 8000.

---

## API endpoints

| Method | Path              | Description                        |
|--------|-------------------|------------------------------------|
| POST   | `/generate`       | Generate a new signed QR code      |
| POST   | `/verify`         | Verify + consume a QR code         |
| GET    | `/list`           | List all issued QR codes           |
| DELETE | `/delete/{id}`    | Delete a QR record                 |
| GET    | `/health`         | Health check                       |

### Generate request body
```json
{ "label": "Ticket #42" }
```

### Verify request body
```json
{ "payload": "...", "signature": "..." }
```

---

## Production notes

- Replace `allow_origins=["*"]` in `main.py` with your frontend domain
- Store `private_key.pem` securely (never commit it)
- Switch from SQLite to PostgreSQL for multi-worker deployments
- Add authentication to `/generate` and `/list` endpoints
"# non_clonable_QR_code_generation" 
