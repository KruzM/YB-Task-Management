from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..auth import get_current_user
from ..database import get_db
from ..schemas.clients import ClientCreate, ClientUpdate, ClientResponse
from ..crud import (
    create_client,
    get_clients,
    get_client_by_id,
    update_client,
    delete_client
)
from ..services.client_defaults import create_standard_client_tasks
from ..schemas.tasks import TaskCreate
from ..crud_utils import tasks as task_crud

router = APIRouter(prefix="/clients", tags=["Clients"])

# GET all clients
@router.get("/", response_model=list[ClientResponse])
def read_clients(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_clients(db)

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
    new_client = create_client(db, client)
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
    return update_client(db, client_id, client)

# DELETE
@router.delete("/{client_id}")
def delete_client_route(
    client_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    delete_client(db, client_id)
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
