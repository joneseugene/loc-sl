from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from pydantic.json import custom_pydantic_encoder

class WardBase(BaseModel):
    name: str
    slug: Optional[str] = None
    lon: float
    lat: float
    region_id: int
    district_id: int
    constituency_id: int

class WardCreate(WardBase):
    pass

class WardRead(WardBase):
    id: int
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

class WardUpdate(BaseModel):
    name: Optional[str] = None
    lon: Optional[float] = None
    lat: Optional[float] = None
    region_id: Optional[int] = None
    district_id: Optional[int] = None
    constituency_id: Optional[int] = None

    class Config:
        orm_mode = True

class WardSoftDelete(BaseModel):
    deleted_reason: Optional[str] = None 

    class Config:
        orm_mode = True
