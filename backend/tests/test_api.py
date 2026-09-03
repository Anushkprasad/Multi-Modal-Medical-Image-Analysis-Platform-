"""
API Integration Tests

Covers all Week-2 deliverable endpoints using FastAPI's TestClient.
No real Gemini API key or PostgreSQL is required — GEMINI_MOCK=true
and SQLite are configured in conftest.py before the app is imported.

Run from the backend/ directory:
    pytest tests/ -v
"""

import io
import struct
import zlib


# ── Helper: generate a minimal valid 1x1 PNG ────────────────────
def _make_tiny_png() -> bytes:
    """
    Build a valid 1x1 white RGB PNG image from scratch.
    Avoids any dependency on Pillow or other image libraries in tests.
    """

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        payload = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + payload + crc

    signature = b"\x89PNG\r\n\x1a\n"
    # IHDR: width=1, height=1, bit_depth=8, colour_type=2 (RGB)
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    # IDAT: filter=0, white pixel (255,255,255)
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
    iend = chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


PNG = _make_tiny_png()  # reused across tests


# ════════════════════════════════════════════════════════════════
# 1. Root endpoint
# ════════════════════════════════════════════════════════════════
class TestRootEndpoint:
    def test_returns_200(self, client):
        assert client.get("/").status_code == 200

    def test_has_message_field(self, client):
        assert "message" in client.get("/").json()

    def test_message_is_string(self, client):
        assert isinstance(client.get("/").json()["message"], str)


# ════════════════════════════════════════════════════════════════
# 2. Simple health check
# ════════════════════════════════════════════════════════════════
class TestHealthEndpoint:
    def test_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_status_healthy(self, client):
        assert client.get("/health").json()["status"] == "healthy"


# ════════════════════════════════════════════════════════════════
# 3. API health check (includes DB status)
# ════════════════════════════════════════════════════════════════
class TestApiHealthEndpoint:
    def test_returns_200(self, client):
        assert client.get("/api/v1/health").status_code == 200

    def test_status_healthy(self, client):
        assert client.get("/api/v1/health").json()["status"] == "healthy"

    def test_has_database_field(self, client):
        data = client.get("/api/v1/health").json()
        assert "database" in data

    def test_database_connected(self, client):
        # SQLite test DB should be reachable
        assert client.get("/api/v1/health").json()["database"] == "connected"


# ════════════════════════════════════════════════════════════════
# 4. POST /api/v1/predict — success cases
# ════════════════════════════════════════════════════════════════
class TestPredictEndpoint:
    def _post_predict(self, client, png=None, content_type="image/png", notes=None):
        png = png or PNG
        files = {"image": ("test.png", io.BytesIO(png), content_type)}
        data = {"clinical_notes": notes} if notes else {}
        return client.post("/api/v1/predict", files=files, data=data)

    def test_returns_200_with_png(self, client):
        assert self._post_predict(client).status_code == 200

    def test_response_has_request_id(self, client):
        data = self._post_predict(client).json()
        assert "request_id" in data
        assert len(data["request_id"]) == 36  # UUID length

    def test_response_has_filename(self, client):
        assert "filename" in self._post_predict(client).json()

    def test_response_has_yolo_result(self, client):
        data = self._post_predict(client).json()
        assert "yolo_result" in data
        assert data["yolo_result"]["status"] == "mock"

    def test_response_has_densenet_result(self, client):
        data = self._post_predict(client).json()
        assert "densenet_result" in data
        assert data["densenet_result"]["status"] == "mock"

    def test_response_has_multimodal_result(self, client):
        data = self._post_predict(client).json()
        assert "multimodal_result" in data
        assert data["multimodal_result"]["status"] == "mock"

    def test_accepts_jpeg_content_type(self, client):
        # Send PNG bytes but declare as JPEG — content-type is what we validate
        assert self._post_predict(client, content_type="image/jpeg").status_code == 200

    def test_accepts_clinical_notes(self, client):
        resp = self._post_predict(client, notes="Patient has fever and cough.")
        assert resp.status_code == 200


# ════════════════════════════════════════════════════════════════
# 5. POST /api/v1/predict — rejection of unsupported types
# ════════════════════════════════════════════════════════════════
class TestPredictValidation:
    def _post_bad_file(self, client, content_type: str):
        files = {"image": ("bad_file", io.BytesIO(b"not an image"), content_type)}
        return client.post("/api/v1/predict", files=files)

    def test_rejects_pdf(self, client):
        assert self._post_bad_file(client, "application/pdf").status_code == 400

    def test_rejects_plain_text(self, client):
        assert self._post_bad_file(client, "text/plain").status_code == 400

    def test_rejects_gif(self, client):
        assert self._post_bad_file(client, "image/gif").status_code == 400

    def test_error_message_mentions_file_type(self, client):
        resp = self._post_bad_file(client, "application/pdf")
        assert "application/pdf" in resp.json()["detail"]


# ════════════════════════════════════════════════════════════════
# 6. Mock Gemini report schema
# ════════════════════════════════════════════════════════════════
class TestMockGeminiReport:
    def _get_report(self, client):
        resp = client.post(
            "/api/v1/predict",
            files={"image": ("test.png", io.BytesIO(PNG), "image/png")},
        )
        return resp.json()["gemini_report"]

    def test_has_impression(self, client):
        assert "impression" in self._get_report(client)

    def test_has_findings(self, client):
        assert "findings" in self._get_report(client)

    def test_has_recommendations(self, client):
        assert "recommendations" in self._get_report(client)

    def test_has_model_summary(self, client):
        assert "model_summary" in self._get_report(client)

    def test_all_fields_are_non_empty_strings(self, client):
        report = self._get_report(client)
        for field in ["impression", "findings", "recommendations", "model_summary"]:
            assert isinstance(report[field], str)
            assert len(report[field]) > 0


# ════════════════════════════════════════════════════════════════
# 7. Audit record creation and retrieval
# ════════════════════════════════════════════════════════════════
class TestAuditEndpoint:
    def _predict_and_get_id(self, client) -> str:
        resp = client.post(
            "/api/v1/predict",
            files={"image": ("test.png", io.BytesIO(PNG), "image/png")},
        )
        assert resp.status_code == 200
        return resp.json()["request_id"]

    def test_audit_record_exists_after_prediction(self, client):
        request_id = self._predict_and_get_id(client)
        assert client.get(f"/api/v1/audit/{request_id}").status_code == 200

    def test_audit_request_id_matches(self, client):
        request_id = self._predict_and_get_id(client)
        data = client.get(f"/api/v1/audit/{request_id}").json()
        assert data["request_id"] == request_id

    def test_audit_has_yolo_result(self, client):
        request_id = self._predict_and_get_id(client)
        data = client.get(f"/api/v1/audit/{request_id}").json()
        assert data["yolo_result"] is not None

    def test_audit_has_gemini_report(self, client):
        request_id = self._predict_and_get_id(client)
        data = client.get(f"/api/v1/audit/{request_id}").json()
        assert data["gemini_report"] is not None
        assert "impression" in data["gemini_report"]

    def test_audit_has_created_at(self, client):
        request_id = self._predict_and_get_id(client)
        data = client.get(f"/api/v1/audit/{request_id}").json()
        assert data["created_at"] is not None

    def test_nonexistent_audit_returns_404(self, client):
        resp = client.get("/api/v1/audit/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_404_detail_mentions_request_id(self, client):
        fake_id = "nonexistent-id"
        resp = client.get(f"/api/v1/audit/{fake_id}")
        assert fake_id in resp.json()["detail"]


# ════════════════════════════════════════════════════════════════
# 8. Regression: live HTTP 500 caused by GEMINI_MOCK frozen at import time
# ════════════════════════════════════════════════════════════════
class TestRegressionHttp500:
    """
    Regression tests for the bug where POST /api/v1/predict returned HTTP 500
    in the live Uvicorn server but passed all automated tests.

    Root cause: gemini_service.py read GEMINI_MOCK at module import time
    (module-level: GEMINI_MOCK = os.getenv(...)), so it was always False
    when uvicorn loaded the module before load_dotenv() had run.

    Fix:
      1. main.py now calls load_dotenv() before importing any app modules.
      2. gemini_service.generate_report() now reads os.getenv("GEMINI_MOCK")
         at call time, not at import time.
    """

    def test_predict_succeeds_with_mock_mode(self, client):
        """
        Core regression: full prediction pipeline must return 200 (not 500)
        when GEMINI_MOCK=true is in the environment.
        conftest.py sets this before the app is imported.
        """
        png = _make_tiny_png()
        resp = client.post(
            "/api/v1/predict",
            files={"image": ("chest_xray.png", io.BytesIO(png), "image/png")},
            data={"clinical_notes": "Patient presents with cough and fever for 3 days."},
        )
        assert resp.status_code == 200, (
            f"Expected 200 but got {resp.status_code}. "
            f"Body: {resp.text}"
        )

    def test_generate_report_reads_env_at_call_time(self):
        """
        Directly verify that generate_report() reads GEMINI_MOCK at call time.
        This is the specific fix for the import-time freeze bug.
        Even if the module was imported without the env var, setting it
        before the call must make the mock path activate.
        """
        import os
        from app.services.gemini_service import generate_report

        original = os.environ.get("GEMINI_MOCK")
        try:
            os.environ["GEMINI_MOCK"] = "true"
            report = generate_report({}, {}, {}, None)
            assert report.impression.startswith("[MOCK]"), (
                "Expected mock report but got real report path"
            )
        finally:
            if original is None:
                os.environ.pop("GEMINI_MOCK", None)
            else:
                os.environ["GEMINI_MOCK"] = original

    def test_predict_response_is_complete(self, client):
        """
        Verify all required fields are present in the prediction response
        — the exact fields the live Swagger request was checking.
        """
        png = _make_tiny_png()
        resp = client.post(
            "/api/v1/predict",
            files={"image": ("chest_xray.png", io.BytesIO(png), "image/png")},
            data={"clinical_notes": "Mild shortness of breath reported."},
        )
        data = resp.json()
        for field in ["request_id", "filename", "yolo_result",
                      "densenet_result", "multimodal_result", "gemini_report"]:
            assert field in data, f"Missing field in response: {field}"

    def test_audit_retrievable_after_live_predict(self, client):
        """
        After the fix, audit retrieval via request_id must also work end-to-end.
        """
        png = _make_tiny_png()
        pred = client.post(
            "/api/v1/predict",
            files={"image": ("chest_xray.png", io.BytesIO(png), "image/png")},
        )
        request_id = pred.json()["request_id"]
        audit = client.get(f"/api/v1/audit/{request_id}")
        assert audit.status_code == 200
        assert audit.json()["request_id"] == request_id

