from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from utils.consts import USER
from utils.database import get_db
from domain.models.district_model import District  
from domain.schema.district_schema import DistrictRead
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from io import StringIO
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
import csv

router = APIRouter(tags=["User Districts"], dependencies=[Depends(has_role(USER))] )

# FETCH ALL
@router.get("/user/districts", response_model=List[DistrictRead])
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
@router.get("/user/districts/{id}", response_model=DistrictRead)
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
@router.get("/user/districts/region/{region_id}", response_model=List[DistrictRead])
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
@router.get("/user/districts/name/{name}", response_model=DistrictRead)
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
    
# EXPORT DISTRICTS
@router.post("/user/districts/export-csv", response_class=StreamingResponse)
def export_districts_csv(db: Session = Depends(get_db)):
    try:
        stmt = select(District).filter(District.active == True, District.deleted == False)
        result = db.execute(stmt)
        districts = result.scalars().all()

        if not districts:
            return error_response(status_code=404, error_message="No districts found to export.")

        # Define CSV headers
        csv_headers = ["No", "Name", "Slug", "Longitude", "Latitude", "RegionId"]

        csv_data = StringIO()
        csv_writer = csv.writer(csv_data)

        # Write the headers to the CSV
        csv_writer.writerow(csv_headers)

        for idx, district in enumerate(districts, start=1):
            csv_writer.writerow([
                idx,  
                district.name,
                district.slug,
                district.lon,
                district.lat,
                district.region_id,
            ])

        csv_data.seek(0)

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
