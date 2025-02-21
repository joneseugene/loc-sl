from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from utils.consts import USER
from utils.database import get_db
from domain.models.ward_model import Ward
from domain.schema.ward_schema import WardRead
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from io import StringIO
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
import csv

router = APIRouter(tags=["User Wards"], dependencies=[Depends(has_role(USER))])

# FETCH ALL
@router.get("/user/wards", response_model=List[WardRead])
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
@router.get("/user/wards/{id}", response_model=WardRead)
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
@router.get("/user/wards/region/{region_id}", response_model=List[WardRead])
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
@router.get("/user/wards/district/{district_id}", response_model=List[WardRead])
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
@router.get("/user/wards/constituency/{constituency_id}", response_model=List[WardRead])
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
@router.get("/user/wards/name/{name}", response_model=WardRead)
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


@router.post("/user/wards/export-csv", response_class=StreamingResponse)
def export_wards_csv(db: Session = Depends(get_db)):
    try:
        stmt = select(Ward).filter(Ward.active == True, Ward.deleted == False)
        result = db.execute(stmt)
        wards = result.scalars().all()

        if not wards:
            return error_response(status_code=404, error_message="No ward found to export.")

        # Define CSV headers
        csv_headers = ["No", "Name", "Slug", "Longitude", "Latitude", "RegionId", "DistrictId", "ConstituencyId"]

        csv_data = StringIO()
        csv_writer = csv.writer(csv_data)

        # Write the headers to the CSV
        csv_writer.writerow(csv_headers)

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

        csv_data.seek(0)

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
