from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from utils.database import get_db
from domain.models.district_model import District  
from domain.schema.district_schema import DistrictCreate, DistrictRead, DistrictSoftDelete, DistrictUpdate
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder

router =  APIRouter(tags=["SuperAdmin Districts"], dependencies=[Depends(has_role(1))] )

# FETCH ALL
@router.get("/super/districts", response_model=List[DistrictRead])
async def get_districts(db: Session = Depends(get_db)):
    try:
        districts = db.query(District).filter(District.active == True, District.deleted == False).all()
        # Serialize each district object
        district_data = [jsonable_encoder(DistrictRead.from_orm(district)) for district in districts]
        
        return success_response(data=district_data)
    except Exception as e:
        print("Error fetching districts:", e)
        return error_response(status_code=500, error_message=str(e))


# FIND BY ID
@router.get("/super/districts/{id}", response_model=DistrictRead)
async def get_district_by_id(id: int, db: Session = Depends(get_db)):
    try:
        district = db.query(District).filter(District.id == id, District.active == True, District.deleted == False).first()
        if not district:
            return error_response(status_code=404, error_message="district not found")
        # Serialize using jsonable_encoder
        return success_response(data=jsonable_encoder(DistrictRead.from_orm(district)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
    

# FIND BY REGION ID
@router.get("/super/districts/{region_id}", response_model=DistrictRead)
async def get_district_by_id(region_id: int, db: Session = Depends(get_db)):
    try:
        district = db.query(District).filter(District.region_id == region_id, District.active == True, District.deleted == False).first()
        if not district:
            return error_response(status_code=404, error_message="district not found")
        # Serialize using jsonable_encoder
        return success_response(data=jsonable_encoder(DistrictRead.from_orm(district)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY NAME
@router.get("/super/districts/name/{name}", response_model=DistrictRead)
async def get_district_by_name(name: str, db: Session = Depends(get_db)):
    try:
        district = db.query(District).filter(District.name == name, District.active == True, District.deleted == False).first()
        if not district:
            return error_response(status_code=404, error_message="district not found")
        # Serialize using jsonable_encoder
        return success_response(data=jsonable_encoder(DistrictRead.from_orm(district)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# CREATE
@router.post("/super/districts", response_model=DistrictCreate)
async def create_district(district: DistrictCreate, db: Session = Depends(get_db)):
    existing_district = db.query(District).filter(District.name == district.name).first()

    if existing_district:
        return error_response(status_code=400, error_message="district already exists")
    new_district = District(name=district.name, lon=district.lon, lat=district.lat, region_id=district.region_id)
    print("New District: ", new_district)
    db.add(new_district)
    db.commit()
    db.refresh(new_district)
    return success_response(data=jsonable_encoder(DistrictRead.from_orm(new_district)))


# UPDATE district
@router.put("/super/districts/{id}", response_model=DistrictRead)
async def update_district(id: int, district_data: DistrictUpdate, db: Session = Depends(get_db)):
    try:
        district = db.query(District).filter(District.id == id).first()
        if not district:
            return error_response(status_code=404, error_message="district not found")
        
        # Update only provided fields
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


# SOFT DELETE district
@router.delete("/super/districts/{id}")
async def soft_delete_district(id: int, delete_data: DistrictSoftDelete, db: Session = Depends(get_db)):
    try:
        district = db.query(District).filter(District.id == id, District.deleted == False).first()
        if not district:
            return error_response(status_code=404, error_message="district not found or already deleted")

        # Soft delete district
        district.deleted = True
        district.deleted_at = datetime.utcnow()
        district.deleted_by = "System"
        district.deleted_reason = delete_data.deleted_reason

        db.commit()
        return success_response(message="district successfully deleted")
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))