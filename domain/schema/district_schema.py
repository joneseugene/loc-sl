from datetime import datetime
from pydantic import BaseModel
from pydantic.json import custom_pydantic_encoder

class DistrictBase(BaseModel):
    name: str
    lon: float
    lat: float
    region_id: int

class DistrictCreate(DistrictBase):
    pass

class DistrictRead(DistrictBase):
    id: int

    
    created_at: datetime
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  
        }
