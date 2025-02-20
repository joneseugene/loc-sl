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
import csv
from io import StringIO
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


# router = APIRouter(tags=["Super Regions"], dependencies=[Depends(has_role(1))] )

router = APIRouter(tags=["Super Regions"])


# FETCH ALL
@router.get("/super/regions", response_model=List[RegionRead])
async def get_regions(db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.active == True, Region.deleted == False)
        result = await db.execute(stmt)
        regions = result.scalars().all()
        
        # Serialize object
        region_data = [jsonable_encoder(RegionRead.from_orm(region)) for region in regions]
        return success_response(data=region_data)
    except Exception as e:
        print("Error fetching regions:", e)
        return error_response(status_code=500, error_message=str(e))


# FIND BY ID
@router.get("/super/regions/{id}", response_model=RegionRead)
async def get_region_by_id(id: int, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.id == id, Region.active == True, Region.deleted == False)
        result = await db.execute(stmt)
        region = result.scalars().first()
        if not region:
            return error_response(status_code=404, error_message="Region not found")
        return success_response(data=jsonable_encoder(RegionRead.from_orm(region)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# FIND BY NAME
@router.get("/super/regions/name/{name}", response_model=RegionRead)
async def get_region_by_name(name: str, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.name == name, Region.active == True, Region.deleted == False)
        result = await db.execute(stmt)
        region = result.scalars().first()
        if not region:
            return error_response(status_code=404, error_message="Region not found")
        return success_response(data=jsonable_encoder(RegionRead.from_orm(region)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# CREATE
@router.post("/super/regions", response_model=RegionCreate)
async def create_region(region: RegionCreate, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.name == region.name)
        result = await db.execute(stmt)
        existing_region = result.scalars().first()
        
        if existing_region:
            return error_response(status_code=400, error_message="Region already exists")

        new_region = Region(name=region.name, lon=region.lon, lat=region.lat)
        db.add(new_region)
        await db.commit()
        await db.refresh(new_region)
        
        return success_response(data=jsonable_encoder(RegionRead.from_orm(new_region)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# UPLOAD REGION
@router.post("/super/regions/upload")
async def upload_regions_csv(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    try:
        df = pd.read_csv(file.file)

        if "name" not in df.columns:
            return error_response(status_code=400, error_message="CSV must contain a 'name' column.")

        processed_regions = []

        for _, row in df.iterrows():
            name = row["name"].strip()

            stmt = select(Region).filter(Region.name == name)
            result = await db.execute(stmt)
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

        await db.commit()
        return success_response(
            message=f"CSV processed successfully. Regions updated/added: {len(processed_regions)}",
            data=processed_regions,
        )

    except pd.errors.EmptyDataError:
        return error_response(status_code=400, error_message="CSV file is empty.")
    except Exception as e:
        return error_response(status_code=500, error_message=f"Error processing CSV: {str(e)}")



@router.get("/super/regions/export", response_class=StreamingResponse)
async def export_regions_csv(db: AsyncSession = Depends(get_db)):
    try:
        # Select regions from the database
        stmt = select(Region).filter(Region.active == True, Region.deleted == False)
        result = await db.execute(stmt)
        regions = result.scalars().all()

        if not regions:
            # If no regions found, return an error response
            return error_response(status_code=404, error_message="No regions found to export.")

        # CSV headers
        csv_headers = ["ID", "Name", "Slug", "Longitude", "Latitude", "Created At", "Created By", "Updated At", "Updated By"]

        # Create CSV data
        csv_data = StringIO()
        csv_writer = csv.writer(csv_data)
        csv_writer.writerow(csv_headers)

        # Write each region's data to the CSV
        for region in regions:
            csv_writer.writerow([  
                region.id,
                region.name,
                region.slug,
                region.lon,
                region.lat,
                region.created_at,
                region.created_by,
                region.updated_at,
                region.updated_by
            ])

        # Move the cursor to the beginning of the CSV data
        csv_data.seek(0)

        # Return the CSV as a StreamingResponse
        return StreamingResponse(
            iter([csv_data.getvalue()]),
            media_type="text/csv",  # Ensure the content type is text/csv
            headers={
                "Content-Disposition": "attachment; filename=regions.csv",  # Force download as CSV
                "Content-Length": str(len(csv_data.getvalue())),  # Set content length
            }
        )

    except Exception as e:
        # If any error occurs, log the exception and return a generic error response
        return error_response(status_code=500, error_message=f"Error generating CSV: {str(e)}")
    

# UPDATE REGION
@router.put("/super/regions/{id}", response_model=RegionRead)
async def update_region(id: int, region_data: RegionUpdate, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.id == id)
        result = await db.execute(stmt)
        region = result.scalars().first()
        
        if not region:
            return error_response(status_code=404, error_message="Region not found")

        update_data = region_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(region, key, value)
            region.updated_at = datetime.utcnow()
            region.updated_by = "System"

        await db.commit()
        await db.refresh(region)
        
        return success_response(data=jsonable_encoder(RegionRead.from_orm(region)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# SOFT DELETE REGION
@router.delete("/super/regions/{id}")
async def soft_delete_region(id: int, delete_data: RegionSoftDelete, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.id == id, Region.deleted == False)
        result = await db.execute(stmt)
        region = result.scalars().first()

        if not region:
            return error_response(status_code=404, error_message="Region not found or already deleted")

        region.deleted = True
        region.deleted_at = datetime.utcnow()
        region.deleted_by = "System"
        region.deleted_reason = delete_data.deleted_reason

        await db.commit()
        return success_response(message="Region successfully deleted")
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
    

