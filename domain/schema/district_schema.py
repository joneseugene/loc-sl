from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from pydantic.json import custom_pydantic_encoder

class DistrictBase(BaseModel):
    name: str
    slug: Optional[str] = None
    lon: float
    lat: float
    region_id: int

class DistrictCreate(DistrictBase):
    pass

class DistrictRead(DistrictBase):
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

class DistrictUpdate(BaseModel):
    name: Optional[str] = None
    lon: Optional[float] = None
    lat: Optional[float] = None
    region_id: Optional[int] = None

    class Config:
        orm_mode = True
        from_attributes = True

class DistrictSoftDelete(BaseModel):
    deleted_reason: Optional[str] = None 

    class Config:
        orm_mode = True
        from_attributes = True
