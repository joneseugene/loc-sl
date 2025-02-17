from datetime import datetime
from pydantic import BaseModel


class RegionBase(BaseModel):
    name: str
    lon: float
    lat: float

class RegionCreate(RegionBase):
    pass

class RegionRead(RegionBase):
    id: int
    created_at: datetime


    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  
        }
