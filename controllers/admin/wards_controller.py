from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from utils.database import get_db
from domain.models.ward_model import Ward
from domain.schema.ward_schema import WardCreate, WardRead, WardSoftDelete, WardUpdate
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
import pandas as pd
import csv
from io import StringIO
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["Admin Wards"], dependencies=[Depends(has_role(2))])

# FETCH ALL
@router.get("/admin/wards", response_model=List[WardRead])
async def get_wards(db: Session = Depends(get_db)):
    try:
        wards = db.query(Ward).filter(Ward.active == True, Ward.deleted == False).all()
        return success_response(data=jsonable_encoder(wards))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# FIND BY ID
@router.get("/admin/wards/{id}", response_model=WardRead)
async def get_ward_by_id(id: int, db: Session = Depends(get_db)):
    try:
        ward = db.query(Ward).filter(Ward.id == id, Ward.active == True, Ward.deleted == False).first()
        if not ward:
            return error_response(status_code=404, error_message="Ward not found")
        return success_response(data=jsonable_encoder(ward))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY REGION ID
@router.get("/admin/wards/region/{region_id}", response_model=List[WardRead])
async def get_wards_by_region_id(region_id: int, db: Session = Depends(get_db)):
    try:
        wards = db.query(Ward).filter(Ward.region_id == region_id, Ward.active == True, Ward.deleted == False).all()
        if not wards:
            return error_response(status_code=404, error_message="No wards found for this region")
        return success_response(data=jsonable_encoder(wards))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
    
# FIND BY DISTRICT ID
@router.get("/admin/wards/district/{district_id}", response_model=List[WardRead])
async def get_wards_by_district_id(district_id: int, db: Session = Depends(get_db)):
    try:
        wards = db.query(Ward).filter(Ward.district_id == district_id, Ward.active == True, Ward.deleted == False).all()
        if not wards:
            return error_response(status_code=404, error_message="No wards found for this district")
        return success_response(data=jsonable_encoder(wards))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY CONSTITUENCY ID
@router.get("/admin/wards/constituency/{constituency_id}", response_model=List[WardRead])
async def get_wards_by_constituency_id(constituency_id: int, db: Session = Depends(get_db)):
    try:
        wards = db.query(Ward).filter(Ward.constituency_id == constituency_id, Ward.active == True, Ward.deleted == False).all()
        if not wards:
            return error_response(status_code=404, error_message="No wards found for this constituency")
        return success_response(data=jsonable_encoder(wards))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# FIND BY NAME
@router.get("/admin/wards/name/{name}", response_model=WardRead)
async def get_ward_by_name(name: str, db: Session = Depends(get_db)):
    try:
        ward = db.query(Ward).filter(Ward.name == name, Ward.active == True, Ward.deleted == False).first()
        if not ward:
            return error_response(status_code=404, error_message="Ward not found")
        return success_response(data=jsonable_encoder(ward))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# CREATE
@router.post("/admin/wards", response_model=WardRead)
async def create_ward(ward: WardCreate, db: Session = Depends(get_db)):
    try:
        existing_ward = db.query(Ward).filter(Ward.name == ward.name).first()
        if existing_ward:
            return error_response(status_code=400, error_message="Ward already exists")

        new_ward = Ward(**ward.dict())
        db.add(new_ward)
        db.commit()
        db.refresh(new_ward)

        return success_response(data=jsonable_encoder(new_ward))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# UPDATE
@router.put("/admin/wards/{id}", response_model=WardRead)
async def update_ward(id: int, ward_data: WardUpdate, db: Session = Depends(get_db)):
    try:
        ward = db.query(Ward).filter(Ward.id == id).first()
        if not ward:
            return error_response(status_code=404, error_message="Ward not found")

        for key, value in ward_data.dict(exclude_unset=True).items():
            setattr(ward, key, value)

        ward.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(ward)

        return success_response(data=jsonable_encoder(ward))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# SOFT DELETE
@router.delete("/admin/wards/{id}")
async def soft_delete_ward(id: int, delete_data: WardSoftDelete, db: Session = Depends(get_db)):
    try:
        ward = db.query(Ward).filter(Ward.id == id, Ward.deleted == False).first()
        if not ward:
            return error_response(status_code=404, error_message="Ward not found or already deleted")

        ward.deleted = True
        ward.deleted_at = datetime.utcnow()
        ward.deleted_by = "System"
        ward.deleted_reason = delete_data.deleted_reason

        db.commit()
        return success_response(message="Ward successfully deleted")
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
