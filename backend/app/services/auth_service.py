from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from ..core.config import Settings, get_settings
from ..core.security import (
    UserRole,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from ..repositories.user_repository import UserRepository


@dataclass
class UserIdentity:
    email: str
    role: UserRole
    hashed_password: str
    name: Optional[str] = None
    active: bool = True


class AuthService:
    """
    Lightweight in-memory authentication service suitable for demos.

    In production this layer would integrate with a persistent identity store
    such as Cognito, Auth0, or a custom user database.
    """

    def __init__(self, settings: Settings | None = None, repository: UserRepository | None = None) -> None:
        self.settings = settings or get_settings()
        self.repository = repository or UserRepository()
        self._users: Dict[str, UserIdentity] = {}
        self._load_users()
        self._bootstrap_users()

    def _load_users(self) -> None:
        raw_users = self.repository.load()
        for email, data in raw_users.items():
            hashed_password = data.get("hashed_password")
            if not hashed_password:
                continue
            try:
                role = UserRole(data.get("role", UserRole.recruiter.value))
            except ValueError:
                role = UserRole.recruiter
            name = data.get("name")
            if not name:
                name = "Administrator" if role == UserRole.admin else "Recruiter"
            self._users[email] = UserIdentity(
                email=email,
                role=role,
                hashed_password=hashed_password,
                name=name,
                active=data.get("active", True),
            )

    def _persist(self) -> None:
        payload = {
            email: {
                "role": identity.role.value,
                "hashed_password": identity.hashed_password,
                "name": identity.name,
                "active": identity.active,
            }
            for email, identity in self._users.items()
        }
        self.repository.save(payload)

    def _bootstrap_users(self) -> None:
        admin_email = self.settings.admin_email.lower()
        if admin_email not in self._users:
            self._users[admin_email] = UserIdentity(
                email=admin_email,
                role=UserRole.admin,
                hashed_password=hash_password(self.settings.admin_password),
                name="Administrator",
                active=True,
            )
        # Ensure demo recruiter exists for UX
        legacy_email = "recruiter@smarthire.local"
        recruiter_email = "recruiter@example.com"
        if legacy_email in self._users and recruiter_email not in self._users:
            legacy_identity = self._users.pop(legacy_email)
            legacy_identity.email = recruiter_email
            legacy_identity.name = legacy_identity.name or "Demo Recruiter"
            self._users[recruiter_email] = legacy_identity
        if recruiter_email not in self._users:
            self._users[recruiter_email] = UserIdentity(
                email=recruiter_email,
                role=UserRole.recruiter,
                hashed_password=hash_password("recruiter123"),
                name="Demo Recruiter",
                active=True,
            )
        self._persist()

    def authenticate(self, email: str, password: str) -> UserIdentity:
        identity = self._users.get(email.lower())
        if not identity or not identity.active or not verify_password(password, identity.hashed_password):
            raise ValueError("Invalid credentials")
        return identity

    def issue_token(self, identity: UserIdentity) -> str:
        return create_access_token(subject=identity.email, role=identity.role, settings=self.settings)

    def verify_token(self, token: str) -> UserIdentity:
        payload = decode_access_token(token, settings=self.settings)
        email = payload.get("sub")
        role = payload.get("role")
        if not email:
            raise ValueError("Token missing subject")
        identity = self._users.get(email.lower())
        if not identity or not identity.active:
            raise ValueError("Unknown user")
        if identity.role.value != role:
            raise ValueError("Role mismatch")
        return identity

    # Administrative helpers -------------------------------------------------

    def list_users(self, roles: Optional[Iterable[UserRole]] = None) -> Dict[str, UserIdentity]:
        if roles is None:
            return {email: identity for email, identity in self._users.items() if identity.active}
        allowed = {role.value for role in roles}
        return {
            email: identity
            for email, identity in self._users.items()
            if identity.active and identity.role.value in allowed
        }

    def create_user(
        self,
        email: str,
        password: str,
        role: UserRole = UserRole.recruiter,
        *,
        name: Optional[str] = None,
    ) -> UserIdentity:
        normalized = email.lower()
        if normalized in self._users:
            raise ValueError("User already exists")
        if not name or not name.strip():
            raise ValueError("Name is required")
        clean_name = name.strip()
        identity = UserIdentity(
            email=normalized,
            role=role,
            hashed_password=hash_password(password),
            name=clean_name,
            active=True,
        )
        self._users[normalized] = identity
        self._persist()
        return identity

    def delete_user(self, email: str) -> None:
        normalized = email.lower()
        if normalized == self.settings.admin_email.lower():
            raise ValueError("Cannot delete primary admin account")
        if normalized not in self._users:
            raise ValueError("User not found")
        del self._users[normalized]
        self._persist()

