from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from utils.consts import ADMIN
from utils.database import get_db
from domain.models.region_model import Region  
from domain.schema.region_schema import RegionCreate, RegionRead, RegionSoftDelete, RegionUpdate
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from io import StringIO
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
import pandas as pd
import csv


router = APIRouter(tags=["Admin Regions"], dependencies=[Depends(has_role(ADMIN))] )

# FETCH ALL
@router.get("/admin/regions", response_model=List[RegionRead])
def get_regions(db: Session = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.active == True, Region.deleted == False)
        result = db.execute(stmt)
        regions = result.scalars().all()
        
        # Serialize object
        region_data = [jsonable_encoder(RegionRead.from_orm(region)) for region in regions]
        return success_response(data=region_data)
    except Exception as e:
        print("Error fetching regions:", e)
        return error_response(status_code=500, error_message=str(e))

# FIND BY ID
@router.get("/admin/regions/{id}", response_model=RegionRead)
def get_region_by_id(id: int, db: Session = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.id == id, Region.active == True, Region.deleted == False)
        result = db.execute(stmt)
        region = result.scalars().first()
        if not region:
            return error_response(status_code=404, error_message="Region not found")
        return success_response(data=jsonable_encoder(RegionRead.from_orm(region)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# FIND BY NAME
@router.get("/admin/regions/name/{name}", response_model=RegionRead)
def get_region_by_name(name: str, db: Session = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.name == name, Region.active == True, Region.deleted == False)
        result = db.execute(stmt)
        region = result.scalars().first()
        if not region:
            return error_response(status_code=404, error_message="Region not found")
        return success_response(data=jsonable_encoder(RegionRead.from_orm(region)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# CREATE
@router.post("/admin/regions", response_model=RegionCreate)
def create_region(region: RegionCreate, db: Session = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.name == region.name)
        result = db.execute(stmt)
        existing_region = result.scalars().first()
        
        if existing_region:
            return error_response(status_code=400, error_message="Region already exists")

        new_region = Region(name=region.name, lon=region.lon, lat=region.lat)
        db.add(new_region)
        db.commit()
        db.refresh(new_region)
        
        return success_response(data=jsonable_encoder(RegionRead.from_orm(new_region)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# UPLOAD REGION
@router.post("/admin/regions/upload")
def upload_regions_csv(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    try:
        df = pd.read_csv(file.file)

        if "name" not in df.columns:
            return error_response(status_code=400, error_message="CSV must contain a 'name' column.")

        processed_regions = []

        for _, row in df.iterrows():
            name = row["name"].strip()

            stmt = select(Region).filter(Region.name == name)
            result = db.execute(stmt)
            existing_region = result.scalars().first()

            if existing_region:
                if existing_region.active is False and existing_region.deleted is True:
                    continue
                existing_region.updated_at = datetime.utcnow()
                existing_region.updated_by = "System"
            else:
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
    except Exception as e:
        return error_response(status_code=500, error_message=f"Error processing CSV: {str(e)}")



@router.post("/admin/regions/export-csv", response_class=StreamingResponse)
def export_regions_csv(db: Session = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.active == True, Region.deleted == False)
        result = db.execute(stmt)
        regions = result.scalars().all()

        if not regions:
            return error_response(status_code=404, error_message="No regions found to export.")

        # Define CSV headers
        csv_headers = ["No", "Name", "Slug", "Longitude", "Latitude"]

        # Create a StringIO object to hold the CSV data
        csv_data = StringIO()
        csv_writer = csv.writer(csv_data)

        # Write the headers to the CSV
        csv_writer.writerow(csv_headers)

        # Add the row number (No) and data for each region
        for idx, region in enumerate(regions, start=1):  # start=1 to begin the "No" column at 1
            csv_writer.writerow([
                idx,  # Row number (No)
                region.name,
                region.slug,
                region.lon,
                region.lat,
            ])

        # Rewind the StringIO object to the beginning for streaming
        csv_data.seek(0)

        # Return the CSV data as a streaming response
        return StreamingResponse(
            iter([csv_data.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=regions.csv",
                "Content-Length": str(len(csv_data.getvalue())),
            }
        )

    except Exception as e:
        # Handle errors and return an appropriate response
        return error_response(status_code=500, error_message=f"Error generating CSV: {str(e)}")



# UPDATE REGION
@router.put("/admin/regions/{id}", response_model=RegionRead)
def update_region(id: int, region_data: RegionUpdate, db: Session = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.id == id)
        result = db.execute(stmt)
        region = result.scalars().first()
        
        if not region:
            return error_response(status_code=404, error_message="Region not found")

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
def soft_delete_region(id: int, delete_data: RegionSoftDelete, db: Session = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.id == id, Region.deleted == False)
        result = db.execute(stmt)
        region = result.scalars().first()

        if not region:
            return error_response(status_code=404, error_message="Region not found or already deleted")

        region.deleted = True
        region.deleted_at = datetime.utcnow()
        region.deleted_by = "System"
        region.deleted_reason = delete_data.deleted_reason

        db.commit()
        return success_response(message="Region successfully deleted")
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
    

