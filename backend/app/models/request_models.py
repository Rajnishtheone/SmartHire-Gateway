from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class AttachmentPayload(BaseModel):
    url: Optional[HttpUrl] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None
    content: Optional[str] = Field(
        default=None,
        description="Base64 encoded payload used for testing without remote download.",
    )


class ManualIngestRequest(BaseModel):
    body: str
    attachments: Optional[List[AttachmentPayload]] = Field(default=None)


class RecruiterCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=100)
