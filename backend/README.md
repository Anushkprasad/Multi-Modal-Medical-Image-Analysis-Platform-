# Multi-Modal Medical Image Analysis — Backend

FastAPI backend for the Multi-Modal Medical Image Analysis Platform.  
Accepts X-ray images, runs AI model pipelines, generates a structured radiology report via Gemini, and logs every prediction to a database.

---

## Architecture

```
backend/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── api/
│   │   └── routes/
│   │       └── prediction.py    # All API endpoints (predict, health, audit)
│   ├── db/
│   │   ├── database.py          # SQLAlchemy engine + session + init_db()
│   │   ├── models.py            # ORM model: prediction_audit table
│   │   └── crud.py              # DB helper functions (save, fetch)
│   ├── schemas/
│   │   └── prediction.py        # Pydantic response models
│   └── services/
│       ├── yolo_service.py      # YOLO detection (placeholder)
│       ├── densenet_service.py  # DenseNet/FAISS similarity (placeholder)
│       ├── multimodal_service.py# Multimodal analysis (placeholder)
│       └── gemini_service.py    # Gemini report generation
├── tests/
│   ├── conftest.py              # Test fixtures + SQLite test DB setup
│   └── test_api.py              # Integration tests for all endpoints
├── .env.example                 # Template — copy to .env and fill in values
└── requirements.txt             # Python dependencies
```

**Request flow** for `POST /api/v1/predict`:
```
Upload image → Validate type → YOLO → DenseNet → Multimodal
    → Gemini report → Save audit record → Return response
```

---

## Installation

```bash
# From the backend/ directory
pip install -r requirements.txt
```

---

## Running the API

```bash
# From the backend/ directory
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

---

## Swagger UI

Once the server is running, open:

```
http://localhost:8000/docs
```

All endpoints, request schemas, and response models are documented there.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable       | Required | Default              | Description                                    |
|----------------|----------|----------------------|------------------------------------------------|
| `GEMINI_API_KEY` | No*    | _(empty)_            | Google AI Studio API key. Not needed if `GEMINI_MOCK=true`. |
| `GEMINI_MODEL`  | No      | `gemini-2.0-flash`   | Gemini model name.                             |
| `GEMINI_MOCK`   | No      | `false`              | Set to `true` to skip real Gemini calls.       |
| `DATABASE_URL`  | No      | `sqlite:///./local_test.db` | SQLAlchemy DB connection string.        |

**Production PostgreSQL example:**
```
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
```

---

## Mock Gemini Mode

Set `GEMINI_MOCK=true` to run the full pipeline without a real API key:

```bash
# Windows
set GEMINI_MOCK=true
python -m uvicorn app.main:app --reload

# Linux / macOS
GEMINI_MOCK=true python -m uvicorn app.main:app --reload
```

The mock response has **exactly the same schema** as a real Gemini response.  
All audit records are still saved to the database in mock mode.

---

## API Endpoints

### `POST /api/v1/predict`
Run the full prediction pipeline on an X-ray image.

**Request** — `multipart/form-data`:
| Field            | Type       | Required | Description                        |
|------------------|------------|----------|------------------------------------|
| `image`          | file       | ✅       | X-ray image (JPEG or PNG)          |
| `clinical_notes` | string     | ❌       | Optional clinical context text     |

**Response** (200):
```json
{
  "request_id": "uuid-string",
  "filename": "xray.png",
  "yolo_result": { "detections": [], "status": "mock" },
  "densenet_result": { "similar_cases": [], "status": "mock" },
  "multimodal_result": { "pathology_probabilities": {}, "grad_cam": null, "status": "mock" },
  "gemini_report": {
    "impression": "...",
    "findings": "...",
    "recommendations": "...",
    "model_summary": "..."
  }
}
```

Returns **400** if the file type is not `image/jpeg`, `image/jpg`, or `image/png`.

---

### `GET /api/v1/audit/{request_id}`
Retrieve the audit record for a previous prediction.

**Response** (200): Full audit record including all model outputs and Gemini report.  
**Response** (404): If no record exists for the given `request_id`.

---

### `GET /api/v1/health`
Returns backend + database connection status.

```json
{ "status": "healthy", "database": "connected" }
```

Never crashes — if the DB is down, `"database"` will show the error message.

---

### `GET /health`
Simple liveness probe. Does not check the database.

---

## Running Tests

```bash
# From the backend/ directory
pytest tests/ -v
```

Tests use:
- `GEMINI_MOCK=true` — no real Gemini API key needed
- SQLite in-memory database — no PostgreSQL needed

---

## Integrating Teammate Models

The three model service files are clearly marked as placeholders:

- `app/services/yolo_service.py` → Replace `call_yolo()` body with real YOLO inference
- `app/services/densenet_service.py` → Replace `call_densenet()` body with real DenseNet + FAISS
- `app/services/multimodal_service.py` → Replace `call_multimodal()` body with real multimodal model

The function **signatures and return shapes are documented** inside each file.  
The prediction route and audit system do not need to change when real models are plugged in.
