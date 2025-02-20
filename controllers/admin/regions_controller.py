from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from utils.database import get_db
from domain.models.region_model import Region  
from domain.schema.region_schema import RegionCreate, RegionRead, RegionSoftDelete, RegionUpdate
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
import pandas as pd


router = APIRouter(tags=["Admin Regions"], dependencies=[Depends(has_role(2))] )

# FETCH ALL
@router.get("/admin/regions", response_model=List[RegionRead])
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
@router.get("/admin/regions/{id}", response_model=RegionRead)
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
@router.get("/admin/regions/name/{name}", response_model=RegionRead)
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
@router.post("/admin/regions", response_model=RegionCreate)
async def create_region(region: RegionCreate, db: Session = Depends(get_db)):
    existing_region = db.query(Region).filter(Region.name == region.name).first()

    if existing_region:
        return error_response(status_code=400, error_message="Region already exists")
    new_region = Region(name=region.name, lon=region.lon, lat=region.lat)
    db.add(new_region)
    db.commit()
    db.refresh(new_region)
    return success_response(data=jsonable_encoder(RegionRead.from_orm(new_region)))

# UPLOAD REGION
@router.post("/admin/regions/upload")
async def upload_regions_csv(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file.file)

        # Check if required column exists
        if "name" not in df.columns:
            return error_response(status_code=400, error_message="CSV must contain a 'name' column.")

        processed_regions = []

        for _, row in df.iterrows():
            name = row["name"].strip()

            # Check if the region exists in the database
            existing_region = db.query(Region).filter(Region.name == name).first()

            if existing_region:
                # If the region is marked deleted, skip it
                if existing_region.active is False and existing_region.deleted is True:
                    continue
                
                # Update existing record
                existing_region.updated_at = datetime.utcnow()
                existing_region.updated_by = "System"

            else:
                # Insert new record
                new_region = Region(
                    name=name,
                    created_at=datetime.utcnow(),
                    created_by="System",
                    updated_at=datetime.utcnow(),
                    updated_by="System",
                    active=True,
                    deleted=False,
                )
                db.add(new_region)
            
            processed_regions.append(name)

        db.commit()
        return success_response(
            message=f"CSV processed successfully. Regions updated/added: {len(processed_regions)}",
            data=processed_regions,
        )

    except pd.errors.EmptyDataError:
        return error_response(status_code=400, error_message="CSV file is empty.")
    except SQLAlchemyError as e:
        db.rollback()
        return error_response(status_code=500, error_message=f"Database error: {str(e)}")
    except Exception as e:
        return error_response(status_code=500, error_message=f"Error processing CSV: {str(e)}")


# UPDATE REGION
@router.put("/admin/regions/{id}", response_model=RegionRead)
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
@router.delete("/admin/regions/{id}")
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
    

