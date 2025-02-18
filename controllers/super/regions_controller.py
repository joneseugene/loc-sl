from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from utils.database import get_db
from domain.models.region_model import Region  
from domain.schema.region_schema import RegionCreate, RegionRead, RegionSoftDelete, RegionUpdate
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder

router = APIRouter(tags=["SuperAdmin Regions"], dependencies=[Depends(has_role(1))] )

# FETCH ALL
@router.get("/super/regions", response_model=List[RegionRead])
async def get_regions(db: Session = Depends(get_db)):
    try:
        regions = db.query(Region).filter(Region.active == True, Region.deleted == False).all()
        # Serialize each region object
        region_data = [jsonable_encoder(RegionRead.from_orm(region)) for region in regions]
        
        return success_response(data=region_data)
    except Exception as e:
        print("Error fetching regions:", e)
        return error_response(status_code=500, error_message=str(e))


# FIND BY ID
@router.get("/super/regions/{id}", response_model=RegionRead)
async def get_region_by_id(id: int, db: Session = Depends(get_db)):
    try:
        region = db.query(Region).filter(Region.id == id, Region.active == True, Region.deleted == False).first()
        if not region:
            return error_response(status_code=404, error_message="Region not found")
        # Serialize using jsonable_encoder
        return success_response(data=jsonable_encoder(RegionRead.from_orm(region)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY NAME
@router.get("/super/regions/name/{name}", response_model=RegionRead)
async def get_region_by_name(name: str, db: Session = Depends(get_db)):
    try:
        region = db.query(Region).filter(Region.name == name, Region.active == True, Region.deleted == False).first()
        if not region:
            return error_response(status_code=404, error_message="Region not found")
        # Serialize using jsonable_encoder
        return success_response(data=jsonable_encoder(RegionRead.from_orm(region)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# CREATE
@router.post("/super/regions", response_model=RegionCreate)
async def create_region(region: RegionCreate, db: Session = Depends(get_db)):
    existing_region = db.query(Region).filter(Region.name == region.name).first()

    if existing_region:
        return error_response(status_code=400, error_message="Region already exists")
    new_region = Region(name=region.name, lon=region.lon, lat=region.lat)
    db.add(new_region)
    db.commit()
    db.refresh(new_region)
    return success_response(data=jsonable_encoder(RegionRead.from_orm(new_region)))

# UPDATE REGION
@router.put("/super/regions/{id}", response_model=RegionRead)
async def update_region(id: int, region_data: RegionUpdate, db: Session = Depends(get_db)):
    try:
        region = db.query(Region).filter(Region.id == id).first()
        if not region:
            return error_response(status_code=404, error_message="Region not found")
        
        # Update only provided fields
        update_data = region_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(region, key, value)

            region.updated_at = datetime.utcnow() 
            region.updated_by = "System"

        db.commit()
        db.refresh(region)

        return success_response(data=jsonable_encoder(RegionRead.from_orm(region)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# SOFT DELETE REGION
@router.delete("/super/regions/{id}")
async def soft_delete_region(id: int, delete_data: RegionSoftDelete, db: Session = Depends(get_db)):
    try:
        region = db.query(Region).filter(Region.id == id, Region.deleted == False).first()
        if not region:
            return error_response(status_code=404, error_message="Region not found or already deleted")

        # Soft delete region
        region.deleted = True
        region.deleted_at = datetime.utcnow()
        region.deleted_by = "System"
        region.deleted_reason = delete_data.deleted_reason

        db.commit()
        return success_response(message="Region successfully deleted")
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))