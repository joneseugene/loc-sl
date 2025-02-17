from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from utils.database import get_db
from domain.models.region_model import Region  
from domain.schema.region_schema import RegionCreate, RegionRead
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder

router = APIRouter(tags=["Regions"])

# FETCH ALL
@router.get("/regions", response_model=List[RegionRead])
async def get_regions(db: Session = Depends(get_db)):
    try:
        regions = db.query(Region).all()
        # Serialize each region object
        region_data = [jsonable_encoder(RegionRead.from_orm(region)) for region in regions]
        
        return success_response(data=region_data)
    except Exception as e:
        print("Error fetching regions:", e)
        return error_response(status_code=500, error_message=str(e))


# FIND BY ID
@router.get("/regions/{id}", response_model=RegionRead)
async def get_region_by_id(id: int, db: Session = Depends(get_db)):
    try:
        region = db.query(Region).filter(Region.id == id).first()
        if not region:
            return error_response(status_code=404, error_message="Region not found")
        # Serialize using jsonable_encoder
        return success_response(data=jsonable_encoder(RegionRead.from_orm(region)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY NAME
@router.get("/regions/name/{name}", response_model=RegionRead)
async def get_region_by_name(name: str, db: Session = Depends(get_db)):
    try:
        region = db.query(Region).filter(Region.name == name).first()
        if not region:
            return error_response(status_code=404, error_message="Region not found")
        # Serialize using jsonable_encoder
        return success_response(data=jsonable_encoder(RegionRead.from_orm(region)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# CREATE
@router.post("/regions", response_model=RegionCreate)
async def create_region(region: RegionCreate, db: Session = Depends(get_db)):
    existing_region = db.query(Region).filter(Region.name == region.name).first()

    if existing_region:
        return error_response(status_code=400, error_message="Region already exists")
    new_region = Region(name=region.name, lon=region.lon, lat=region.lat)
    db.add(new_region)
    db.commit()
    db.refresh(new_region)
    return success_response(data=jsonable_encoder(RegionRead.from_orm(new_region)))