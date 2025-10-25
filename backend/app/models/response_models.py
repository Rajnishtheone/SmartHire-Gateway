from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserProfile(BaseModel):
    email: str
    role: str
    name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class CandidateRecord(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    education: Optional[str] = None
    experience: Optional[str] = None
    last_job_title: Optional[str] = None
    source: str
    received_at: datetime
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    notes: Optional[str] = None


class CandidateListResponse(BaseModel):
    count: int
    items: List[CandidateRecord]


class IngestResponse(BaseModel):
    status: str
    candidate: CandidateRecord


class RecruiterListResponse(BaseModel):
    count: int
    items: List[UserProfile]
