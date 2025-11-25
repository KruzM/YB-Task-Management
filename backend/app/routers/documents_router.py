from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from backend.app.database import get_db
from backend.app.auth import get_current_user
from backend.app.models import User
from backend.app.schemas.documents import (
    DocumentCreate,
    DocumentResponse,
    DocumentListResponse,
    DocumentPurgeRequest,
    DocumentPurgeApproval,
    MissingDocumentReport,
    DocumentTypeEnum,
)
from backend.app.crud_utils import documents as doc_crud

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentTypeEnum = Form(...),
    client_id: int = Form(...),
    account_id: Optional[int] = Form(None),
    month: Optional[int] = Form(None),
    year: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a document with automatic folder placement"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Read file content
    file_content = await file.read()
    
    # Create document record
    document_data = DocumentCreate(
        document_type=document_type,
        client_id=client_id,
        account_id=account_id,
        month=month,
        year=year,
    )
    
    document = doc_crud.create_document(
        db=db,
        document_data=document_data,
        file_content=file_content,
        original_filename=file.filename,
        mime_type=file.content_type,
        uploaded_by=current_user.id,
    )
    
    return document


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    client_id: Optional[int] = None,
    account_id: Optional[int] = None,
    document_type: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List documents with optional filters"""
    documents = doc_crud.list_documents(
        db=db,
        client_id=client_id,
        account_id=account_id,
        document_type=document_type,
        month=month,
        year=year,
        status=status,
    )
    return {"documents": documents, "total": len(documents)}


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single document"""
    document = doc_crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download a document file"""
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    document = doc_crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    storage_base = doc_crud.get_documents_storage_path()
    file_path = storage_base / document.file_path
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=str(file_path),
        filename=document.original_filename,
        media_type=document.mime_type or "application/octet-stream",
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document (requires admin for purge)"""
    # Regular users can only delete their own uploads or if they're admin
    document = doc_crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not current_user.is_admin and document.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")
    
    success = doc_crud.delete_document(db, document_id, performed_by=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return


@router.get("/clients/{client_id}/missing", response_model=List[MissingDocumentReport])
def get_missing_documents(
    client_id: int,
    account_id: Optional[int] = None,
    document_type: str = "statement",
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of missing documents for a client"""
    missing = doc_crud.get_missing_documents(
        db=db,
        client_id=client_id,
        account_id=account_id,
        document_type=document_type,
        year=year,
    )
    return missing


@router.post("/purge/approve/{document_id}")
def approve_purge(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve document purge (requires admin, needs two approvals)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = doc_crud.approve_document_purge(db, document_id, current_user.id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/purge/execute")
def execute_purges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute approved document purges (requires admin)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    purged_count = doc_crud.execute_purge_approved_documents(db, current_user.id)
    return {"message": f"Purged {purged_count} documents", "count": purged_count}

