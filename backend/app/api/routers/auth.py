from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...models.request_models import LoginRequest
from ...models.response_models import TokenResponse, UserProfile
from ...services.auth_service import AuthService, UserIdentity
from ..dependencies import get_auth_service, get_current_user

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        identity = auth_service.authenticate(email=payload.email, password=payload.password)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    token = auth_service.issue_token(identity)
    return TokenResponse(access_token=token, token_type="bearer", user=_profile_from_identity(identity))


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: UserIdentity = Depends(get_current_user)) -> UserProfile:
    return _profile_from_identity(current_user)


def _profile_from_identity(identity: UserIdentity) -> UserProfile:
    return UserProfile(email=identity.email, role=identity.role.value, name=identity.name)
