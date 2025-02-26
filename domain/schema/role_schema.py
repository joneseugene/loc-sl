from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class RoleRead(RoleBase):
    id: int
    active: bool
    deleted: bool
    created_at: datetime
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RoleUpdate(BaseModel):
    name: Optional[str] = None

    class Config:
        from_attributes = True


class RoleSoftDelete(BaseModel):
    deleted_reason: Optional[str] = None

    class Config:
        from_attributes = True