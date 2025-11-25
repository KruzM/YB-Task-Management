from pydantic import BaseModel, Field
from typing import Optional, List


class ContactBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactResponse(ContactBase):
    id: int

    class Config:
        orm_mode = True


class AccountBase(BaseModel):
    name: str
    account_type: Optional[str] = None
    institution: Optional[str] = None
    number_last4: Optional[str] = None
    status: Optional[str] = "active"


class AccountCreate(AccountBase):
    client_id: Optional[int] = None


class AccountResponse(AccountBase):
    id: int
    client_id: int

    class Config:
        orm_mode = True


class ClientGroupBase(BaseModel):
    name: str
    description: Optional[str] = None


class ClientGroupCreate(ClientGroupBase):
    pass


class ClientGroupResponse(ClientGroupBase):
    id: int
    members: List = Field(default_factory=list)

    class Config:
        orm_mode = True


class ClientGroupMembershipResponse(BaseModel):
    id: int
    role: Optional[str] = None
    group: ClientGroupResponse

    class Config:
        orm_mode = True


class ClientBase(BaseModel):
    name: str
    primary_contact: Optional[str] = None
    primary_email: Optional[str] = None
    primary_phone: Optional[str] = None
    status: Optional[str] = "active"
    cpa: Optional[str] = None
    manager: Optional[str] = None
    billing_frequency: Optional[str] = None
    autopay: Optional[bool] = False
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    primary_contact: Optional[str] = None
    primary_email: Optional[str] = None
    primary_phone: Optional[str] = None
    status: Optional[str] = None
    cpa: Optional[str] = None
    manager: Optional[str] = None
    billing_frequency: Optional[str] = None
    autopay: Optional[bool] = None
    notes: Optional[str] = None


class ClientResponse(ClientBase):
    id: int
    tasks: List = Field(default_factory=list)
    assignments: List = Field(default_factory=list)
    contacts: List[ContactResponse] = Field(default_factory=list)
    accounts: List[AccountResponse] = Field(default_factory=list)
    groups: List[ClientGroupMembershipResponse] = Field(default_factory=list)

    class Config:
        orm_mode = True


class ClientListResponse(BaseModel):
    clients: List[ClientResponse]
    total: int


class ContactListResponse(BaseModel):
    contacts: List[ContactResponse]
    total: int


class AccountListResponse(BaseModel):
    accounts: List[AccountResponse]
    total: int


class ClientGroupListResponse(BaseModel):
    groups: List[ClientGroupResponse]
    total: int
