from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ...models.response_models import CandidateListResponse
from ...services.storage_service import StorageService
from ...services.auth_service import UserIdentity
from ..dependencies import get_storage_service, require_any_role
from ...core.security import UserRole

router = APIRouter(prefix="/candidates")


@router.get("", response_model=CandidateListResponse)
async def list_candidates(
    limit: int = Query(default=20, ge=1, le=200),
    storage_service: StorageService = Depends(get_storage_service),
    _: UserIdentity = Depends(require_any_role([UserRole.recruiter, UserRole.admin])),
) -> CandidateListResponse:
    records = storage_service.list_recent_candidates(limit=limit)
    return CandidateListResponse(items=records, count=len(records))
