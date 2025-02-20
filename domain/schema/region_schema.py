from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class RegionBase(BaseModel):
    name: str
    slug: Optional[str] = None
    lon: float
    lat: float

class RegionCreate(RegionBase):
    pass

class RegionRead(RegionBase):
    id: int
    active: bool
    deleted: bool
    created_at: datetime
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


    class Config:
        orm_mode = True
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  
        }

class RegionUpdate(BaseModel):
    name: Optional[str] = None
    lon: Optional[float] = None
    lat: Optional[float] = None

    class Config:
        orm_mode = True
        from_attributes = True

class RegionSoftDelete(BaseModel):
    deleted_reason: Optional[str] = None 

    class Config:
        orm_mode = True
        from_attributes = True
