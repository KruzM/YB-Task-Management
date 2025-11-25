"""
CRUD operations for document management
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import os
import hashlib
import shutil

from backend.app import models
from backend.app.schemas.documents import DocumentCreate, DocumentStatusEnum
from backend.app.crud_utils.audit import log_audit_action


def get_documents_storage_path() -> Path:
    """Get the base storage path for documents"""
    project_root = Path(__file__).resolve().parents[3]
    storage_path = project_root / "documents"
    storage_path.mkdir(exist_ok=True)
    return storage_path


def generate_document_filename(
    client_id: int,
    account_id: Optional[int],
    document_type: str,
    month: Optional[int],
    year: Optional[int],
    original_filename: str,
) -> tuple[str, str]:
    """
    Generate a standardized filename and folder path for a document.
    Returns (filename, relative_path)
    """
    storage_base = get_documents_storage_path()
    
    # Create folder structure: documents/{client_id}/{account_id or 'general'}/{year}/{month or 'misc'}
    client_folder = storage_base / str(client_id)
    if account_id:
        account_folder = client_folder / str(account_id)
    else:
        account_folder = client_folder / "general"
    
    if year:
        year_folder = account_folder / str(year)
        if month:
            month_folder = year_folder / f"{month:02d}"
        else:
            month_folder = year_folder / "misc"
    else:
        month_folder = account_folder / "misc"
    
    month_folder.mkdir(parents=True, exist_ok=True)
    
    # Generate filename: {type}_{YYYY-MM}_{original_name}
    ext = Path(original_filename).suffix
    if year and month:
        date_part = f"{year}-{month:02d}"
    elif year:
        date_part = str(year)
    else:
        date_part = datetime.now().strftime("%Y-%m")
    
    safe_name = Path(original_filename).stem.replace(" ", "_")
    new_filename = f"{document_type}_{date_part}_{safe_name}{ext}"
    
    # Ensure unique filename
    counter = 1
    base_name = new_filename
    while (month_folder / new_filename).exists():
        name_part = Path(base_name).stem
        ext_part = Path(base_name).suffix
        new_filename = f"{name_part}_{counter}{ext_part}"
        counter += 1
    
    relative_path = str(month_folder.relative_to(storage_base) / new_filename)
    return new_filename, relative_path


def save_uploaded_file(file_content: bytes, relative_path: str) -> str:
    """Save uploaded file to storage"""
    storage_base = get_documents_storage_path()
    full_path = storage_base / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(full_path, "wb") as f:
        f.write(file_content)
    
    return str(full_path)


def create_document(
    db: Session,
    document_data: DocumentCreate,
    file_content: bytes,
    original_filename: str,
    mime_type: Optional[str],
    uploaded_by: int,
) -> models.Document:
    """Create a new document record and save the file"""
    # Generate filename and path
    filename, relative_path = generate_document_filename(
        client_id=document_data.client_id,
        account_id=document_data.account_id,
        document_type=document_data.document_type.value,
        month=document_data.month,
        year=document_data.year,
        original_filename=original_filename,
    )
    
    # Save file
    full_path = save_uploaded_file(file_content, relative_path)
    file_size = len(file_content)
    
    # Create database record
    document = models.Document(
        filename=filename,
        original_filename=original_filename,
        file_path=relative_path,
        file_size=file_size,
        mime_type=mime_type,
        document_type=document_data.document_type.value,
        status=DocumentStatusEnum.received.value,
        client_id=document_data.client_id,
        account_id=document_data.account_id,
        month=document_data.month,
        year=document_data.year,
        uploaded_by=uploaded_by,
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Log audit
    log_audit_action(
        db=db,
        action="document_uploaded",
        entity_type="document",
        entity_id=document.id,
        performed_by=uploaded_by,
        details={
            "filename": original_filename,
            "document_type": document_data.document_type.value,
            "client_id": document_data.client_id,
        },
    )
    
    return document


def list_documents(
    db: Session,
    client_id: Optional[int] = None,
    account_id: Optional[int] = None,
    document_type: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    status: Optional[str] = None,
) -> List[models.Document]:
    """List documents with optional filters"""
    query = db.query(models.Document)
    
    if client_id:
        query = query.filter(models.Document.client_id == client_id)
    if account_id:
        query = query.filter(models.Document.account_id == account_id)
    if document_type:
        query = query.filter(models.Document.document_type == document_type)
    if month:
        query = query.filter(models.Document.month == month)
    if year:
        query = query.filter(models.Document.year == year)
    if status:
        query = query.filter(models.Document.status == status)
    
    return query.order_by(models.Document.uploaded_at.desc()).all()


def get_document(db: Session, document_id: int) -> Optional[models.Document]:
    """Get a single document by ID"""
    return db.query(models.Document).filter(models.Document.id == document_id).first()


def get_missing_documents(
    db: Session,
    client_id: Optional[int] = None,
    account_id: Optional[int] = None,
    document_type: str = "statement",
    year: Optional[int] = None,
) -> List[dict]:
    """
    Identify missing documents by comparing expected vs received.
    For statements, expects monthly documents.
    """
    if not year:
        year = datetime.now().year
    
    # Get all received documents for the criteria
    received = list_documents(
        db=db,
        client_id=client_id,
        account_id=account_id,
        document_type=document_type,
        year=year,
        status=DocumentStatusEnum.received.value,
    )
    
    # Build set of received (month, account_id) pairs
    received_set = set()
    for doc in received:
        key = (doc.month, doc.account_id)
        received_set.add(key)
    
    # Determine which months/accounts should have documents
    # For simplicity, assume all active accounts need monthly statements
    if client_id:
        accounts = db.query(models.Account).filter(
            models.Account.client_id == client_id,
            models.Account.status == "active",
        ).all()
        
        if account_id:
            accounts = [a for a in accounts if a.id == account_id]
    else:
        accounts = []
    
    missing = []
    for month in range(1, 13):
        for account in accounts:
            key = (month, account.id)
            if key not in received_set:
                missing.append({
                    "client_id": client_id,
                    "account_id": account.id,
                    "document_type": document_type,
                    "month": month,
                    "year": year,
                    "status": "missing",
                })
        # Also check for general (no account) documents
        if not accounts:
            key = (month, None)
            if key not in received_set:
                missing.append({
                    "client_id": client_id,
                    "account_id": None,
                    "document_type": document_type,
                    "month": month,
                    "year": year,
                    "status": "missing",
                })
    
    return missing


def delete_document(db: Session, document_id: int, performed_by: int) -> bool:
    """Delete a document (soft delete by marking as purged)"""
    document = get_document(db, document_id)
    if not document:
        return False
    
    # Mark as purged
    document.status = DocumentStatusEnum.purged.value
    document.purged_at = datetime.utcnow()
    
    # Delete physical file
    storage_base = get_documents_storage_path()
    full_path = storage_base / document.file_path
    if full_path.exists():
        try:
            full_path.unlink()
        except Exception as e:
            print(f"Error deleting file {full_path}: {e}")
    
    db.commit()
    
    log_audit_action(
        db=db,
        action="document_deleted",
        entity_type="document",
        entity_id=document_id,
        performed_by=performed_by,
    )
    
    return True


def mark_client_left(db: Session, client_id: int, left_date: Optional[datetime] = None) -> None:
    """Mark all client documents for purge hold (6 months)"""
    if not left_date:
        left_date = datetime.utcnow()
    
    purge_hold_until = left_date + timedelta(days=180)  # 6 months
    
    documents = db.query(models.Document).filter(
        models.Document.client_id == client_id,
        models.Document.status != DocumentStatusEnum.purged.value,
    ).all()
    
    for doc in documents:
        doc.client_left_date = left_date
        doc.purge_hold_until = purge_hold_until
        doc.status = DocumentStatusEnum.pending_purge.value
    
    db.commit()


def approve_document_purge(
    db: Session,
    document_id: int,
    approver_id: int,
) -> dict:
    """
    Approve document purge. Requires two admins.
    Returns status indicating if purge can proceed.
    """
    document = get_document(db, document_id)
    if not document:
        return {"error": "Document not found"}
    
    if document.status != DocumentStatusEnum.pending_purge.value:
        return {"error": "Document is not pending purge"}
    
    # Check if already approved by this user
    if document.purge_approved_by_1 == approver_id or document.purge_approved_by_2 == approver_id:
        return {"error": "You have already approved this purge"}
    
    # Assign first or second approval
    if document.purge_approved_by_1 is None:
        document.purge_approved_by_1 = approver_id
        db.commit()
        return {
            "status": "first_approval",
            "message": "First approval recorded. Second admin approval required.",
        }
    elif document.purge_approved_by_2 is None:
        document.purge_approved_by_2 = approver_id
        document.purge_approved_at = datetime.utcnow()
        db.commit()
        return {
            "status": "approved",
            "message": "Both approvals received. Document can be purged.",
        }
    else:
        return {"error": "Document already has two approvals"}
    
    log_audit_action(
        db=db,
        action="document_purge_approved",
        entity_type="document",
        entity_id=document_id,
        performed_by=approver_id,
    )


def execute_purge_approved_documents(db: Session, performed_by: Optional[int] = None) -> int:
    """
    Purge documents that have been approved by two admins and passed the hold period.
    Returns count of purged documents.
    """
    now = datetime.utcnow()
    
    documents_to_purge = db.query(models.Document).filter(
        models.Document.status == DocumentStatusEnum.pending_purge.value,
        models.Document.purge_approved_by_1.isnot(None),
        models.Document.purge_approved_by_2.isnot(None),
        models.Document.purge_hold_until <= now,
    ).all()
    
    purged_count = 0
    for document in documents_to_purge:
        # Check if 7 years have passed since client left
        if document.client_left_date:
            years_since_left = (now - document.client_left_date).days / 365.25
            if years_since_left >= 7:
                # Use system user ID (1) if performed_by is None
                actor_id = performed_by if performed_by is not None else 1
                if delete_document(db, document.id, actor_id):
                    purged_count += 1
    
    return purged_count

