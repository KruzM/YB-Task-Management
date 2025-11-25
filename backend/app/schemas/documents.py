from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class DocumentTypeEnum(str, Enum):
    statement = "statement"
    tax_document = "tax_document"
    misc = "misc"


class DocumentStatusEnum(str, Enum):
    received = "received"
    missing = "missing"
    pending_purge = "pending_purge"
    purged = "purged"


class DocumentCreate(BaseModel):
    document_type: DocumentTypeEnum
    client_id: int
    account_id: Optional[int] = None
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = Field(None, ge=2000, le=2100)
    description: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    document_type: str
    status: str
    client_id: int
    account_id: Optional[int]
    month: Optional[int]
    year: Optional[int]
    uploaded_by: int
    uploaded_at: datetime
    client_left_date: Optional[datetime]
    purge_hold_until: Optional[datetime]
    purge_approved_by_1: Optional[int]
    purge_approved_by_2: Optional[int]
    purge_approved_at: Optional[datetime]
    purged_at: Optional[datetime]

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class DocumentPurgeRequest(BaseModel):
    document_ids: list[int]
    reason: Optional[str] = None


class DocumentPurgeApproval(BaseModel):
    purge_request_id: int  # This could be a separate table, but for simplicity, we'll use document IDs
    approve: bool
    reason: Optional[str] = None


class MissingDocumentReport(BaseModel):
    client_id: int
    account_id: Optional[int]
    document_type: str
    month: Optional[int]
    year: Optional[int]
    status: str  # "missing" or "received"

