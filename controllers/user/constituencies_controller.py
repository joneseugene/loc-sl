from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from utils.consts import USER
from utils.database import get_db
from domain.models.constituency_model import Constituency 
from domain.schema.constituency_schema import ConstituencyRead
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from io import StringIO
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
import csv

router =  APIRouter(tags=["User Constituencies"], dependencies=[Depends(has_role(USER))] )

# FETCH ALL
@router.get("/user/constituencies", response_model=List[ConstituencyRead])
def get_constituencies(db: Session = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.active == True, Constituency.deleted == False)
        result = db.execute(stmt)
        constituencies = result.scalars().all()

        # Serialize object
        constituency_data = [jsonable_encoder(ConstituencyRead.from_orm(constituency)) for constituency in constituencies]
        return success_response(data=constituency_data)
    except Exception as e:
        print("Error fetching constituencies:", e)
        return error_response(status_code=500, error_message=str(e))

# FIND BY ID
@router.get("/user/constituencies/{id}", response_model=ConstituencyRead)
def get_constituency_by_id(id: int, db: Session = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.id == id, Constituency.active == True, Constituency.deleted == False)
        result = db.execute(stmt)
        constituency = result.scalar_one_or_none()

        if not constituency:
            return error_response(status_code=404, error_message="constituency not found")
        
        return success_response(data=jsonable_encoder(ConstituencyRead.from_orm(constituency)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# FIND BY REGION ID
@router.get("/user/constituencies/region/{region_id}", response_model=List[ConstituencyRead])
def get_constituency_by_region_id(region_id: int, db: Session = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.region_id == region_id, Constituency.active == True, Constituency.deleted == False)
        result = db.execute(stmt)
        constituencies = result.scalars().all()

        if not constituencies:
            return error_response(status_code=404, error_message="constituency not found")
        
        return success_response(data=jsonable_encoder([ConstituencyRead.from_orm(constituency) for constituency in constituencies]))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# FIND BY DISTRICT ID
@router.get("/user/constituencies/district/{district_id}", response_model=List[ConstituencyRead])
def get_constituency_by_district_id(district_id: int, db: Session = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.district_id == district_id, Constituency.active == True, Constituency.deleted == False)
        result = db.execute(stmt)
        constituencies = result.scalars().all()

        if not constituencies:
            return error_response(status_code=404, error_message="constituency not found")
        
        return success_response(data=jsonable_encoder([ConstituencyRead.from_orm(constituency) for constituency in constituencies]))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# FIND BY CONSTITUENCY ID
@router.get("/user/constituencies/constituency/{constituencyn_id}", response_model=List[ConstituencyRead])
def get_constituency_by_constituency_id(constituency_id: int, db: Session = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.constituency_id == constituency_id, Constituency.active == True, Constituency.deleted == False)
        result = db.execute(stmt)
        constituencies = result.scalars().all()

        if not constituencies:
            return error_response(status_code=404, error_message="constituency not found")
        
        return success_response(data=jsonable_encoder([ConstituencyRead.from_orm(constituency) for constituency in constituencies]))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# FIND BY NAME
@router.get("/user/constituencies/name/{name}", response_model=ConstituencyRead)
def get_constituency_by_name(name: str, db: Session = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.name == name, Constituency.active == True, Constituency.deleted == False)
        result = db.execute(stmt)
        constituency = result.scalar_one_or_none()

        if not constituency:
            return error_response(status_code=404, error_message="constituency not found")
        
        return success_response(data=jsonable_encoder(ConstituencyRead.from_orm(constituency)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# EXPORT CONSTITUENCIES
@router.post("/user/constituencies/export-csv", response_class=StreamingResponse)
def export_constituencies_csv(db: Session = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.active == True, Constituency.deleted == False)
        result = db.execute(stmt)
        constituencies = result.scalars().all()

        if not constituencies:
            return error_response(status_code=404, error_message="No constituencies found to export.")

        # Define CSV headers
        csv_headers = ["No", "Name", "Slug", "Longitude", "Latitude", "RegionId", "DistrictId"]

        csv_data = StringIO()
        csv_writer = csv.writer(csv_data)

        csv_writer.writerow(csv_headers)

        for idx, constituency in enumerate(constituencies, start=1):  
            csv_writer.writerow([
                idx,
                constituency.name,
                constituency.slug,
                constituency.lon,
                constituency.lat,
                constituency.region_id,
                constituency.district_id,
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
        return error_response(status_code=500, error_message=f"Error generating CSV: {str(e)}")


