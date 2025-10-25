from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field


class UserProfile(BaseModel):
    email: str
    role: str
    name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class CandidateStatus(str, Enum):
    NEW = "new"
    APPROVED = "approved"
    REJECTED = "rejected"
    SELECTED = "selected"
    INTERVIEW = "interview"
    ARCHIVED = "archived"


class CandidateRecord(BaseModel):
    candidate_id: str = Field(default_factory=lambda: uuid4().hex)
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
    status: CandidateStatus = CandidateStatus.NEW
    sheet_row: Optional[int] = Field(default=None, exclude=True)


class CandidateListResponse(BaseModel):
    count: int
    items: List[CandidateRecord]


class CandidateBoardResponse(BaseModel):
    new: List[CandidateRecord] = Field(default_factory=list)
    approved: List[CandidateRecord] = Field(default_factory=list)
    interview: List[CandidateRecord] = Field(default_factory=list)
    selected: List[CandidateRecord] = Field(default_factory=list)
    rejected: List[CandidateRecord] = Field(default_factory=list)


class IngestResponse(BaseModel):
    status: str
    candidate: CandidateRecord


class RecruiterListResponse(BaseModel):
    count: int
    items: List[UserProfile]
