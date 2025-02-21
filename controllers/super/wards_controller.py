from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from utils.consts import SUPER
from utils.database import get_db
from domain.models.ward_model import Ward
from domain.schema.ward_schema import WardCreate, WardRead, WardSoftDelete, WardUpdate
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from io import StringIO
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
import pandas as pd
import csv

router = APIRouter(tags=["Super Wards"], dependencies=[Depends(has_role(SUPER))])

# FETCH ALL
@router.get("/super/wards", response_model=List[WardRead])
def get_wards(db: Session = Depends(get_db)):
    try:
        stmt = select(Ward).filter(Ward.active == True, Ward.deleted == False)
        result = db.execute(stmt)
        wards = result.scalars().all()

        # Serialize object
        ward_data = [jsonable_encoder(WardRead.from_orm(ward)) for ward in wards]
        return success_response(data=ward_data)
    except Exception as e:
        print("Error fetching wards:", e)
        return error_response(status_code=500, error_message=str(e))

# FIND BY ID
@router.get("/super/wards/{id}", response_model=WardRead)
def get_ward_by_id(id: int, db: Session = Depends(get_db)):
    try:
        stmt = select(Ward).filter(Ward.id == id, Ward.active == True, Ward.deleted == False)
        result = db.execute(stmt)
        ward = result.scalar_one_or_none()

        if not ward:
            return error_response(status_code=404, error_message="ward not found")
        
        return success_response(data=jsonable_encoder(WardRead.from_orm(ward)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY REGION ID
@router.get("/super/wards/region/{region_id}", response_model=List[WardRead])
def get_ward_by_region_id(region_id: int, db: Session = Depends(get_db)):
    try:
        stmt = select(Ward).filter(Ward.region_id == region_id, Ward.active == True, Ward.deleted == False)
        result = db.execute(stmt)
        wards = result.scalars().all()

        if not wards:
            return error_response(status_code=404, error_message="ward not found")
        
        return success_response(data=jsonable_encoder([WardRead.from_orm(ward) for ward in wards]))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY DISTRICT ID
@router.get("/super/wards/district/{district_id}", response_model=List[WardRead])
def get_ward_by_district_id(district_id: int, db: Session = Depends(get_db)):
    try:
        stmt = select(Ward).filter(Ward.district_id == district_id, Ward.active == True, Ward.deleted == False)
        result = db.execute(stmt)
        wards = result.scalars().all()

        if not wards:
            return error_response(status_code=404, error_message="ward not found")
        
        return success_response(data=jsonable_encoder([WardRead.from_orm(ward) for ward in wards]))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY CONSTITUENCY ID
@router.get("/super/wards/constituency/{constituency_id}", response_model=List[WardRead])
def get_wards_by_constituency_id(constituency_id: int, db: Session = Depends(get_db)):
    try:
        stmt = select(Ward).filter(Ward.constituency_id == constituency_id, Ward.active == True, Ward.deleted == False)
        result = db.execute(stmt)
        wards = result.scalars().all()

        if not wards:
            return error_response(status_code=404, error_message="constituency not found")
        
        return success_response(data=jsonable_encoder([WardRead.from_orm(constituency) for constituency in wards]))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY NAME
@router.get("/super/wards/name/{name}", response_model=WardRead)
def get_ward_by_name(name: str, db: Session = Depends(get_db)):
    try:
        stmt = select(Ward).filter(Ward.name == name, Ward.active == True, Ward.deleted == False)
        result = db.execute(stmt)
        ward = result.scalar_one_or_none()

        if not ward:
            return error_response(status_code=404, error_message="ward not found")
        
        return success_response(data=jsonable_encoder(WardRead.from_orm(ward)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# CREATE
@router.post("/super/wards", response_model=WardCreate)
def create_ward(ward: WardCreate, db: Session = Depends(get_db)):
    try:
        stmt = select(Ward).filter(Ward.name == ward.name)
        result = db.execute(stmt)
        existing_ward = result.scalar_one_or_none()

        if existing_ward:
            return error_response(status_code=400, error_message="ward already exists")
        
        new_data = Ward(name=ward.name, lon=ward.lon, lat=ward.lat, region_id=ward.region_id, district_id=ward.district_id, constituency_id=ward.constituency_id)
        db.add(new_data)
        db.commit()
        db.refresh(new_data)

        return success_response(data=jsonable_encoder(WardRead.from_orm(new_data)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# UPDATE WARD
@router.put("/super/wards/{id}", response_model=WardRead)
def update_ward(id: int, ward_data: WardUpdate, db: Session = Depends(get_db)):
    try:
        stmt = select(Ward).filter(Ward.id == id)
        result = db.execute(stmt)
        ward = result.scalar_one_or_none()

        if not ward:
            return error_response(status_code=404, error_message="ward not found")
        
        update_data = ward_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(ward, key, value)

        ward.updated_at = datetime.utcnow()
        ward.updated_by = "System"

        db.commit()
        db.refresh(ward)

        return success_response(data=jsonable_encoder(WardRead.from_orm(ward)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# SOFT DELETE WARD
@router.delete("/super/wards/{id}")
def soft_delete_ward(id: int, delete_data: WardSoftDelete, db: Session = Depends(get_db)):
    try:
        stmt = select(Ward).filter(Ward.id == id, Ward.deleted == False)
        result = db.execute(stmt)
        ward = result.scalar_one_or_none()

        if not ward:
            return error_response(status_code=404, error_message="ward not found or already deleted")

        ward.deleted = True
        ward.deleted_at = datetime.utcnow()
        ward.deleted_by = "System"
        ward.deleted_reason = delete_data.deleted_reason

        db.commit()

        return success_response(message="ward successfully deleted")
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
    

# UPLOAD CONSTITUENCIES
@router.post("/super/wards/upload")
def upload_wards_csv(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    try:
        df = pd.read_csv(file.file)

        if "name" not in df.columns:
            return error_response(status_code=400, error_message="csv must contain a 'name' column.")

        processed_wards = []

        for _, row in df.iterrows():
            name = row["name"].strip()

            stmt = select(Ward).filter(Ward.name == name)
            result = db.execute(stmt)
            existing_wards = result.scalars().first()

            if existing_wards:
                if existing_wards.active is False and existing_wards.deleted is True:
                    continue
                existing_wards.updated_at = datetime.utcnow()
                existing_wards.updated_by = "System"
            else:
                new_wards = Ward(
                    name=name,
                    created_at=datetime.utcnow(),
                    created_by="System",
                    updated_at=datetime.utcnow(),
                    updated_by="System",
                    active=True,
                    deleted=False,
                )
                db.add(new_wards)
            
            processed_wards.append(name)

        db.commit()
        return success_response(
            message=f"csv processed successfully. Ward updated/added: {len(processed_wards)}",
            data=processed_wards,
        )

    except pd.errors.EmptyDataError:
        return error_response(status_code=400, error_message="csv file is empty.")
    except Exception as e:
        return error_response(status_code=500, error_message=f"Error processing CSV: {str(e)}")



@router.post("/super/wards/export-csv", response_class=StreamingResponse)
def export_wards_csv(db: Session = Depends(get_db)):
    try:
        stmt = select(Ward).filter(Ward.active == True, Ward.deleted == False)
        result = db.execute(stmt)
        wards = result.scalars().all()

        if not wards:
            return error_response(status_code=404, error_message="No ward found to export.")

        # Define CSV headers
        csv_headers = ["No", "Name", "Slug", "Longitude", "Latitude", "RegionId", "DistrictId", "ConstituencyId"]

        # Create a StringIO object to hold the CSV data
        csv_data = StringIO()
        csv_writer = csv.writer(csv_data)

        # Write the headers to the CSV
        csv_writer.writerow(csv_headers)

        # Add the row number (No) and data for each ward
        for idx, ward in enumerate(wards, start=1):  
            csv_writer.writerow([
                idx, 
                ward.name,
                ward.slug,
                ward.lon,
                ward.lat,
                ward.region_id,
                ward.district_id,
                ward.constituency_id
            ])

        # Rewind the StringIO object to the beginning for streaming
        csv_data.seek(0)

        # Return the CSV data as a streaming response
        return StreamingResponse(
            iter([csv_data.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=constituencies.csv",
                "Content-Length": str(len(csv_data.getvalue())),
            }
        )

    except Exception as e:
        # Handle errors and return an appropriate response
        return error_response(status_code=500, error_message=f"Error generating CSV: {str(e)}")
