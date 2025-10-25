from __future__ import annotations

from backend.app.models.request_models import AttachmentPayload
from backend.app.services.parsing_service import ParsingService


def test_parsing_basic_entities(test_settings):
    service = ParsingService(settings=test_settings)
    text = "Hello, I am Jane Doe. Contact me at jane@example.com or +1 222 333 4444. I have 5 years of experience in Python and AWS."
    record = service.parse_payload(body=text, attachments=None, source="test")
    assert record.full_name in {"Jane Doe", "Jane"}
    assert record.email == "jane@example.com"
    assert "python" in record.skills
    assert record.phone.replace(" ", "").endswith("4444")


def test_parsing_with_attachment(monkeypatch, tmp_path, test_settings):
    # Fake OCR service to avoid heavy dependencies in unit test
    class DummyOCR:
        def extract_from_attachments(self, attachments):
            return []

    service = ParsingService(settings=test_settings, ocr_service=DummyOCR())
    record = service.parse_payload(
        body="Candidate located in Bengaluru.",
        attachments=[AttachmentPayload(content="", filename="resume.pdf")],
        source="test",
    )
    assert record.location in {None, "Bengaluru"}
