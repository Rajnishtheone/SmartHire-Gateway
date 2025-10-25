from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...core.security import UserRole
from ...models.request_models import RecruiterCreateRequest
from ...models.response_models import RecruiterListResponse, UserProfile
from ...services.auth_service import AuthService, UserIdentity
from ..dependencies import get_auth_service, require_role

router = APIRouter(prefix="/admin/users", dependencies=[Depends(require_role(UserRole.admin))])


@router.get("", response_model=RecruiterListResponse)
async def list_recruiters(
    auth_service: AuthService = Depends(get_auth_service),
) -> RecruiterListResponse:
    users = auth_service.list_users(roles=[UserRole.recruiter])
    return RecruiterListResponse(
        items=[
            UserProfile(email=identity.email, role=identity.role.value, name=identity.name)
            for identity in users.values()
        ],
        count=len(users),
    )


@router.post("", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def create_recruiter(
    payload: RecruiterCreateRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserProfile:
    try:
        identity = auth_service.create_user(
            email=payload.email,
            password=payload.password,
            role=UserRole.recruiter,
            name=payload.name,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return UserProfile(email=identity.email, role=identity.role.value, name=identity.name)


@router.delete("/{email}", status_code=status.HTTP_200_OK, response_model=dict[str, str])
async def delete_recruiter(
    email: str,
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    try:
        auth_service.delete_user(email)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"status": "deleted"}
