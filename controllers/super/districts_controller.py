from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from utils.consts import SUPER
from utils.database import get_db
from domain.models.district_model import District  
from domain.schema.district_schema import DistrictCreate, DistrictRead, DistrictSoftDelete, DistrictUpdate
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from io import StringIO
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
import pandas as pd
import csv

router = APIRouter(tags=["Super Districts"], dependencies=[Depends(has_role(SUPER))] )

# FETCH ALL
@router.get("/super/districts", response_model=List[DistrictRead])
def get_districts(db: Session = Depends(get_db)):
    try:
        stmt = select(District).filter(District.active == True, District.deleted == False)
        result = db.execute(stmt)
        districts = result.scalars().all()

        # Serialize each district object
        district_data = [jsonable_encoder(DistrictRead.from_orm(district)) for district in districts]

        return success_response(data=district_data)
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY ID
@router.get("/super/districts/{id}", response_model=DistrictRead)
def get_district_by_id(id: int, db: Session = Depends(get_db)):
    try:
        stmt = select(District).filter(District.id == id, District.active == True, District.deleted == False)
        result = db.execute(stmt)
        district = result.scalars().first()
        if not district:
            return error_response(status_code=404, error_message="District not found")
        
        return success_response(data=jsonable_encoder(DistrictRead.from_orm(district)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY REGION ID
@router.get("/super/districts/region/{region_id}", response_model=List[DistrictRead])
def get_districts_by_region(region_id: int, db: Session = Depends(get_db)):
    try:
        stmt = select(District).filter(District.region_id == region_id, District.active == True, District.deleted == False)
        result = db.execute(stmt)
        districts = result.scalars().all()

        if not districts:
            return error_response(status_code=404, error_message="No districts found for this region")

        district_data = [jsonable_encoder(DistrictRead.from_orm(district)) for district in districts]
        return success_response(data=district_data)
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY NAME
@router.get("/super/districts/name/{name}", response_model=DistrictRead)
def get_district_by_name(name: str, db: Session = Depends(get_db)):
    try:
        stmt = select(District).filter(District.name == name, District.active == True, District.deleted == False)
        result = db.execute(stmt)
        district = result.scalars().first()
        if not district:
            return error_response(status_code=404, error_message="District not found")
        
        return success_response(data=jsonable_encoder(DistrictRead.from_orm(district)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# CREATE
@router.post("/super/districts", response_model=DistrictCreate)
def create_district(district: DistrictCreate, db: Session = Depends(get_db)):
    try:
        stmt = select(District).filter(District.name == district.name)
        result = db.execute(stmt)
        existing_district = result.scalars().first()

        if existing_district:
            return error_response(status_code=400, error_message="District already exists")

        new_district = District(
            name=district.name, lon=district.lon, lat=district.lat, region_id=district.region_id
        )
        db.add(new_district)
        db.commit()
        db.refresh(new_district)
        return success_response(data=jsonable_encoder(DistrictRead.from_orm(new_district)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# UPDATE DISTRICT
@router.put("/super/districts/{id}", response_model=DistrictRead)
def update_district(id: int, district_data: DistrictUpdate, db: Session = Depends(get_db)):
    try:
        stmt = select(District).filter(District.id == id)
        result = db.execute(stmt)
        district = result.scalars().first()

        if not district:
            return error_response(status_code=404, error_message="District not found")

        update_data = district_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(district, key, value)

        district.updated_at = datetime.utcnow()
        district.updated_by = "System"

        db.commit()
        db.refresh(district)

        return success_response(data=jsonable_encoder(DistrictRead.from_orm(district)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# UPLOAD DISTRICTS
@router.post("/super/districts/upload")
def upload_districts_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        df = pd.read_csv(file.file)

        if "name" not in df.columns or "region_id" not in df.columns:
            return error_response(status_code=400, error_message="CSV must contain 'name' and 'region_id' columns.")

        processed_districts = []

        for _, row in df.iterrows():
            name = row["name"].strip()
            region_id = row["region_id"]

            stmt = select(District).filter(District.name == name)
            result = db.execute(stmt)
            existing_district = result.scalars().first()

            if existing_district:
                if existing_district.active is False and existing_district.deleted is True:
                    continue
                existing_district.updated_at = datetime.utcnow()
                existing_district.updated_by = "System"
            else:
                new_district = District(
                    name=name,
                    region_id=region_id,
                    created_at=datetime.utcnow(),
                    created_by="System",
                    updated_at=datetime.utcnow(),
                    updated_by="System",
                    active=True,
                    deleted=False,
                )
                db.add(new_district)

            processed_districts.append(name)

        db.commit()
        return success_response(
            message=f"CSV processed successfully. Districts updated/added: {len(processed_districts)}",
            data=processed_districts,
        )

    except pd.errors.EmptyDataError:
        return error_response(status_code=400, error_message="CSV file is empty.")
    except Exception as e:
        return error_response(status_code=500, error_message=f"Error processing CSV: {str(e)}")


# EXPORT DISTRICTS
@router.post("/super/districts/export-csv", response_class=StreamingResponse)
def export_districts_csv(db: Session = Depends(get_db)):
    try:
        stmt = select(District).filter(District.active == True, District.deleted == False)
        result = db.execute(stmt)
        districts = result.scalars().all()

        if not districts:
            return error_response(status_code=404, error_message="No districts found to export.")

        # Define CSV headers
        csv_headers = ["No", "Name", "Region ID", "Longitude", "Latitude", "RegionId"]

        # Create a StringIO object to hold the CSV data
        csv_data = StringIO()
        csv_writer = csv.writer(csv_data)

        # Write the headers to the CSV
        csv_writer.writerow(csv_headers)

        # Add the row number (No) and data for each district
        for idx, district in enumerate(districts, start=1):
            csv_writer.writerow([
                idx,  # Row number (No)
                district.name,
                district.region_id,
                district.lon,
                district.lat,
            ])

        # Rewind the StringIO object to the beginning for streaming
        csv_data.seek(0)

        # Return the CSV data as a streaming response
        return StreamingResponse(
            iter([csv_data.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=districts.csv",
                "Content-Length": str(len(csv_data.getvalue())),
            }
        )

    except Exception as e:
        return error_response(status_code=500, error_message=f"Error generating CSV: {str(e)}")


# SOFT DELETE DISTRICT
@router.delete("/super/districts/{id}")
def soft_delete_district(id: int, delete_data: DistrictSoftDelete, db: Session = Depends(get_db)):
    try:
        stmt = select(District).filter(District.id == id, District.deleted == False)
        result = db.execute(stmt)
        district = result.scalars().first()

        if not district:
            return error_response(status_code=404, error_message="District not found or already deleted")

        district.deleted = True
        district.deleted_at = datetime.utcnow()
        district.deleted_by = "System"
        district.deleted_reason = delete_data.deleted_reason

        db.commit()
        return success_response(message="District successfully deleted")
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
