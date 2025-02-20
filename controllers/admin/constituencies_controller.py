from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from utils.database import get_db
from domain.models.constituency_model import Constituency 
from domain.schema.constituency_schema import ConstituencyCreate, ConstituencyRead, ConstituencySoftDelete, ConstituencyUpdate
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
import pandas as pd
import csv
from io import StringIO
from fastapi.responses import StreamingResponse

router =  APIRouter(tags=["Admin Constituencies"], dependencies=[Depends(has_role(2))] )

# FETCH ALL
@router.get("/admin/constituencies", response_model=List[ConstituencyRead])
async def get_constituencies(db: Session = Depends(get_db)):
    try:
        constituencies = db.query(Constituency).filter(Constituency.active == True, Constituency.deleted == False).all()
        # Serialize each constituency object
        constituency_data = [jsonable_encoder(ConstituencyRead.from_orm(constituency)) for constituency in constituencies]
        
        return success_response(data=constituency_data)
    except Exception as e:
        print("Error fetching co:", e)
        return error_response(status_code=500, error_message=str(e))


# FIND BY ID
@router.get("/admin/constituencies/{id}", response_model=ConstituencyRead)
async def get_constituency_by_id(id: int, db: Session = Depends(get_db)):
    try:
        constituency = db.query(Constituency).filter(Constituency.id == id, Constituency.active == True, Constituency.deleted == False).first()
        if not constituency:
            return error_response(status_code=404, error_message="constituency not found")
        # Serialize using jsonable_encoder
        return success_response(data=jsonable_encoder(ConstituencyRead.from_orm(constituency)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
    

# FIND BY REGION ID
@router.get("/admin/constituencies/region/{region_id}", response_model=List[ConstituencyRead])
async def get_constituency_by_region_id(region_id: int, db: Session = Depends(get_db)):
    try:
        constituency = db.query(Constituency).filter(Constituency.region_id == region_id, Constituency.active == True, Constituency.deleted == False).first()
        if not constituency:
            return error_response(status_code=404, error_message="constituency not found")
        # Serialize using jsonable_encoder
        return success_response(data=jsonable_encoder(ConstituencyRead.from_orm(constituency)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
    

# FIND BY DISTRICT ID
@router.get("/admin/constituencies/district/{district_id}", response_model=List[ConstituencyRead])
async def get_constituency_by_district_id(district_id: int, db: Session = Depends(get_db)):
    try:
        constituency = db.query(constituency).filter(Constituency.district_id == district_id, Constituency.active == True, Constituency.deleted == False).first()
        if not constituency:
            return error_response(status_code=404, error_message="constituency not found")
        # Serialize using jsonable_encoder
        return success_response(data=jsonable_encoder(ConstituencyRead.from_orm(constituency)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY NAME
@router.get("/admin/constituencies/name/{name}", response_model=ConstituencyRead)
async def get_constituency_by_name(name: str, db: Session = Depends(get_db)):
    try:
        constituency = db.query(Constituency).filter(Constituency.name == name, Constituency.active == True, Constituency.deleted == False).first()
        if not constituency:
            return error_response(status_code=404, error_message="constituency not found")
        # Serialize using jsonable_encoder
        return success_response(data=jsonable_encoder(ConstituencyRead.from_orm(constituency)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# CREATE
@router.post("/admin/constituencies", response_model=ConstituencyCreate)
async def create_constituency(constituency: ConstituencyCreate, db: Session = Depends(get_db)):
    existing_constituency = db.query(Constituency).filter(Constituency.name == constituency.name).first()

    if existing_constituency:
        return error_response(status_code=400, error_message="constituency already exists")
    new_data = Constituency(name=constituency.name, lon=constituency.lon, lat=constituency.lat, region_id=constituency.region_id)
    print("New Constituency: ",new_data)
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    return success_response(data=jsonable_encoder(ConstituencyRead.from_orm(new_data)))


# UPDATE constituency
@router.put("/admin/constituencies/{id}", response_model=ConstituencyRead)
async def update_constituency(id: int, constituency_data: ConstituencyUpdate, db: Session = Depends(get_db)):
    try:
        constituency = db.query(Constituency).filter(Constituency.id == id).first()
        if not constituency:
            return error_response(status_code=404, error_message="constituency not found")
        
        # Update only provided fields
        update_data = constituency_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(constituency, key, value)

            constituency.updated_at = datetime.utcnow() 
            constituency.updated_by = "System"

        db.commit()
        db.refresh(constituency)

        return success_response(data=jsonable_encoder(ConstituencyRead.from_orm(constituency)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# SOFT DELETE constituency
@router.delete("/admin/constituencies/{id}")
async def soft_delete_constituency(id: int, delete_data: ConstituencySoftDelete, db: Session = Depends(get_db)):
    try:
        constituency = db.query(Constituency).filter(Constituency.id == id, Constituency.deleted == False).first()
        if not constituency:
            return error_response(status_code=404, error_message="constituency not found or already deleted")

        # Soft delete constituency
        constituency.deleted = True
        constituency.deleted_at = datetime.utcnow()
        constituency.deleted_by = "System"
        constituency.deleted_reason = delete_data.deleted_reason

        db.commit()
        return success_response(message="constituency successfully deleted")
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))