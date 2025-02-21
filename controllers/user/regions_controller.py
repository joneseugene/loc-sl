from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, UploadFile, File
from utils.consts import USER
from utils.database import get_db
from domain.models.region_model import Region  
from domain.schema.region_schema import RegionCreate, RegionRead
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from io import StringIO
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
import pandas as pd
import csv


router = APIRouter(tags=["User Regions"], dependencies=[Depends(has_role(USER))] )

# FETCH ALL
@router.get("/user/regions", response_model=List[RegionRead])
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
@router.get("/user/regions/{id}", response_model=RegionRead)
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
@router.get("/user/regions/name/{name}", response_model=RegionRead)
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
@router.post("/user/regions", response_model=RegionCreate)
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


@router.post("/user/regions/export-csv", response_class=StreamingResponse)
def export_regions_csv(db: Session = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.active == True, Region.deleted == False)
        result = db.execute(stmt)
        regions = result.scalars().all()

        if not regions:
            return error_response(status_code=404, error_message="No regions found to export.")

        # Define CSV headers
        csv_headers = ["No", "Name", "Slug", "Longitude", "Latitude"]

        csv_data = StringIO()
        csv_writer = csv.writer(csv_data)

        csv_writer.writerow(csv_headers)

        for idx, region in enumerate(regions, start=1):  
            csv_writer.writerow([
                idx,
                region.name,
                region.slug,
                region.lon,
                region.lat,
            ])

        csv_data.seek(0)

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

