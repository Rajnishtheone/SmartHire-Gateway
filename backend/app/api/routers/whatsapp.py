from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, Response, status

from ...models.request_models import ManualIngestRequest
from ...models.response_models import IngestResponse
from ...services.ingestion_service import IngestionService
from ...services.whatsapp_service import WhatsAppService
from ..dependencies import get_ingestion_service, get_whatsapp_service

router = APIRouter(prefix="/whatsapp")


@router.post("/webhook", include_in_schema=False)
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    twilio_signature: str | None = Header(default=None, alias="X-Twilio-Signature"),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service),
) -> Response:
    form = await request.form()
    payload = {key: value for key, value in form.multi_items()}

    if not whatsapp_service.validate_request(
        signature=twilio_signature,
        url=str(request.url),
        payload=payload,
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid Twilio signature")

    background_tasks.add_task(whatsapp_service.process_incoming_message, payload)
    return Response(content="Message received", media_type="text/plain")


@router.post("/manual-ingest", response_model=IngestResponse, summary="Developer helper to ingest resumes")
async def manual_ingest(
    request: ManualIngestRequest,
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> IngestResponse:
    record = ingestion_service.ingest_payload(
        source="manual",
        body=request.body,
        attachments=request.attachments or [],
    )
    return IngestResponse(status="processed", candidate=record)
