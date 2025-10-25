from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ...models.request_models import CandidateStatusUpdateRequest
from ...models.response_models import CandidateBoardResponse, CandidateListResponse, CandidateRecord, CandidateStatus
from ...services.storage_service import StorageService
from ...services.auth_service import UserIdentity
from ..dependencies import get_storage_service, require_any_role
from ...core.security import UserRole

router = APIRouter(prefix="/candidates")


@router.get("", response_model=CandidateListResponse)
async def list_candidates(
    limit: int = Query(default=20, ge=1, le=200),
    status: CandidateStatus | None = Query(default=None),
    storage_service: StorageService = Depends(get_storage_service),
    _: UserIdentity = Depends(require_any_role([UserRole.recruiter, UserRole.admin])),
) -> CandidateListResponse:
    records = storage_service.list_candidates(status=status, limit=limit)
    return CandidateListResponse(items=records, count=len(records))


@router.get("/board", response_model=CandidateBoardResponse)
async def candidate_board(
    storage_service: StorageService = Depends(get_storage_service),
    _: UserIdentity = Depends(require_any_role([UserRole.recruiter, UserRole.admin])),
) -> CandidateBoardResponse:
    return storage_service.get_candidate_board()


@router.patch("/{candidate_id}/status", response_model=CandidateRecord)
async def update_candidate_status(
    candidate_id: str,
    request: CandidateStatusUpdateRequest,
    storage_service: StorageService = Depends(get_storage_service),
    _: UserIdentity = Depends(require_any_role([UserRole.recruiter, UserRole.admin])),
) -> CandidateRecord:
    try:
        return storage_service.update_candidate_status(candidate_id, request.status)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found") from exc


@router.delete("/{candidate_id}", response_model=CandidateRecord)
async def delete_candidate(
    candidate_id: str,
    storage_service: StorageService = Depends(get_storage_service),
    _: UserIdentity = Depends(require_any_role([UserRole.recruiter, UserRole.admin])),
) -> CandidateRecord:
    try:
        return storage_service.delete_candidate(candidate_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found") from exc


@router.delete("", response_model=dict)
async def delete_candidates_by_status(
    status: CandidateStatus = Query(...),
    storage_service: StorageService = Depends(get_storage_service),
    _: UserIdentity = Depends(require_any_role([UserRole.recruiter, UserRole.admin])),
) -> dict:
    removed = storage_service.delete_candidates_by_status(status)
    return {"removed": removed}
