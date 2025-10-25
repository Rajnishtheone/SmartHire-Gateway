from __future__ import annotations

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..core.config import Settings, get_settings
from ..core.security import UserRole
from ..repositories.audit_repository import AuditRepository
from ..repositories.drive_repository import DriveRepository
from ..repositories.sheets_repository import SheetsRepository
from ..services.auth_service import AuthService, UserIdentity
from ..services.ingestion_service import IngestionService
from ..services.parsing_service import ParsingService
from ..services.storage_service import StorageService
from ..services.whatsapp_service import WhatsAppService


bearer_scheme = HTTPBearer(auto_error=False)


def get_app_settings() -> Settings:
    return get_settings()


def get_auth_service(settings: Settings = Depends(get_app_settings)) -> AuthService:
    return AuthService(settings=settings)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserIdentity:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Credentials missing")
    try:
        return auth_service.verify_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def require_role(role: UserRole):
    def _enforce(user: UserIdentity = Depends(get_current_user)) -> UserIdentity:
        if user.role != role:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
        return user

    return _enforce


def require_any_role(roles: list[UserRole]):
    allowed = set(roles)

    def _enforce(user: UserIdentity = Depends(get_current_user)) -> UserIdentity:
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
        return user

    return _enforce


def get_parsing_service(
    settings: Settings = Depends(get_app_settings),
) -> ParsingService:
    return ParsingService(settings=settings)


def get_storage_service(
    settings: Settings = Depends(get_app_settings),
) -> StorageService:
    sheets_repo = SheetsRepository(settings=settings)
    drive_repo = DriveRepository(settings=settings)
    audit_repo = AuditRepository()
    return StorageService(
        sheets_repository=sheets_repo,
        drive_repository=drive_repo,
        audit_repository=audit_repo,
        settings=settings,
    )


def get_ingestion_service(
    parsing_service: ParsingService = Depends(get_parsing_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> IngestionService:
    return IngestionService(
        parsing_service=parsing_service,
        storage_service=storage_service,
    )


def get_whatsapp_service(
    settings: Settings = Depends(get_app_settings),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> WhatsAppService:
    return WhatsAppService(settings=settings, ingestion_service=ingestion_service)
