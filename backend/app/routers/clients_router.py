from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.orm import Session
from ..auth import get_current_user
from ..database import get_db
from ..schemas.clients import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientListResponse,
    ContactCreate,
    ContactResponse,
    ContactListResponse,
    AccountCreate,
    AccountResponse,
    AccountListResponse,
    ClientGroupCreate,
    ClientGroupResponse,
    ClientGroupListResponse,
)
from ..crud import (
    create_client,
    get_clients,
    get_client_by_id,
    update_client,
    delete_client,
    create_contact,
    list_contacts,
    attach_contact_to_client,
    create_account,
    list_accounts_for_client,
    create_client_group,
    list_client_groups,
    add_client_to_group,
)
from ..services.client_defaults import create_standard_client_tasks
from ..schemas.tasks import TaskCreate
from ..crud_utils import tasks as task_crud

router = APIRouter(prefix="/clients", tags=["Clients"])

# GET all clients
@router.get("/", response_model=ClientListResponse)
def read_clients(
    search: Optional[str] = Query(default=None, description="Search by name or contact"),
    status: Optional[str] = Query(default=None, description="Filter by client status"),
    group: Optional[str] = Query(default=None, description="Filter by client group name"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    clients = get_clients(db, search=search, status=status, group_name=group)
    return {"clients": clients, "total": len(clients)}

# GET single client
@router.get("/{client_id}", response_model=ClientResponse)
def read_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_client_by_id(db, client_id)

# POST create client
@router.post("/", response_model=ClientResponse)
def create_client_route(
    client: ClientCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    new_client = create_client(db, client, performed_by=current_user.id)
    create_standard_client_tasks(db, new_client.id, creator_id=current_user.id)
    return new_client

# PUT update
@router.put("/{client_id}", response_model=ClientResponse)
def update_client_route(
    client_id: int,
    client: ClientUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_client(db, client_id, client, performed_by=current_user.id)

# DELETE
@router.delete("/{client_id}")
def delete_client_route(
    client_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    delete_client(db, client_id, performed_by=current_user.id)
    return {"message": "Client deleted"}


@router.post("/{client_id}/recurring-tasks", response_model=ClientResponse)
def add_custom_recurring_task(
    client_id: int,
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if task.client_id != client_id:
        raise HTTPException(status_code=400, detail="Client mismatch between URL and payload")
    if not task.is_recurring:
        raise HTTPException(status_code=400, detail="Recurring tasks must be marked is_recurring=True")

    task_crud.create_task(db, task, creator_id=current_user.id)
    return get_client_by_id(db, client_id)


@router.post("/{client_id}/contacts", response_model=ClientResponse)
def add_contact_to_client(
    client_id: int,
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    new_contact = create_contact(db, contact)
    attach_contact_to_client(db, client_id=client_id, contact_id=new_contact.id)
    return get_client_by_id(db, client_id)


@router.get("/{client_id}/contacts", response_model=ContactListResponse)
def list_client_contacts(
    client_id: int,
    search: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    contacts = list_contacts(db, search=search)
    linked = [c for c in contacts if any(link.client_id == client_id for link in c.links)]
    return {"contacts": linked, "total": len(linked)}


@router.post("/{client_id}/accounts", response_model=AccountResponse)
def create_account_for_client(
    client_id: int,
    account: AccountCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    created = create_account(db, account, client_id=client_id)
    return created


@router.get("/{client_id}/accounts", response_model=AccountListResponse)
def list_accounts(
    client_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    accounts = list_accounts_for_client(db, client_id)
    return {"accounts": accounts, "total": len(accounts)}


@router.post("/groups", response_model=ClientGroupResponse)
def create_group(
    group: ClientGroupCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return create_client_group(db, group)


@router.get("/groups", response_model=ClientGroupListResponse)
def list_groups(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    groups = list_client_groups(db)
    return {"groups": groups, "total": len(groups)}


@router.post("/{client_id}/groups/{group_id}", response_model=ClientResponse)
def add_client_group_membership(
    client_id: int,
    group_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    add_client_to_group(db, client_id=client_id, group_id=group_id)
    return get_client_by_id(db, client_id)
