from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    organization: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    role_id: int
    active: bool
    deleted: bool
    created_at: datetime
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    organization: Optional[str] = None
    role_id: Optional[int] = None

    class Config:
        orm_mode = True


class UserSoftDelete(BaseModel):
    deleted_reason: Optional[str] = None

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str