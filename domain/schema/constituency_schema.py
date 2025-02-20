from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from pydantic.json import custom_pydantic_encoder

class ConstituencyBase(BaseModel):
    name: str
    slug: Optional[str] = None
    lon: float
    lat: float
    region_id: int
    district_id: int

class ConstituencyCreate(ConstituencyBase):
    pass

class ConstituencyRead(ConstituencyBase):
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

class ConstituencyUpdate(BaseModel):
    name: Optional[str] = None
    lon: Optional[float] = None
    lat: Optional[float] = None
    region_id: Optional[int] = None
    district_id: Optional[int] = None

    class Config:
        orm_mode = True

class ConstituencySoftDelete(BaseModel):
    deleted_reason: Optional[str] = None 

    class Config:
        orm_mode = True
