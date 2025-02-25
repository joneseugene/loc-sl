from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from domain.models.district_model import District
from domain.models.region_model import Region
from utils.consts import SUPER
from utils.database import get_db
from domain.models.constituency_model import Constituency 
from domain.schema.constituency_schema import ConstituencyCreate, ConstituencyRead, ConstituencySoftDelete, ConstituencyUpdate
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from io import StringIO
from utils.pagination_sorting import PaginationParams, paginate_and_sort
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
import pandas as pd
import csv


#router =  APIRouter(tags=["Super Constituencies"], dependencies=[Depends(has_role(SUPER))] )
router =  APIRouter(tags=["Super Constituencies"])

# FETCH ALL
@router.get("/super/constituencies", response_model=List[ConstituencyRead])
def get_constituencies(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),  
    limit: int = Query(10, ge=1, le=100),  
    sort_field: Optional[str] = Query(None),
    sort_order: Optional[str] = Query("asc"),
    id: Optional[int] = Query(None),
    name: Optional[str] = Query(None),
    slug: Optional[str] = Query(None),
    lon: Optional[float] = Query(None),
    lat: Optional[float] = Query(None),
    region_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    created_at: Optional[str] = Query(None),
    created_by: Optional[str] = Query(None),
    updated_at: Optional[str] = Query(None),
    updated_by: Optional[str] = Query(None)
):
    try:
        stmt = select(
            Constituency,
            Region.name.label("region_name"),
            District.name.label("district_name")
        ).join(Region, Constituency.region_id == Region.id
        ).join(District, Constituency.district_id == District.id
        ).filter(Constituency.active == True, Constituency.deleted == False)

        # Filters
        if id is not None:
            stmt = stmt.filter(Constituency.id == id)
        if name:
            stmt = stmt.filter(Constituency.name.ilike(f"%{name}%"))
        if slug:
            stmt = stmt.filter(Constituency.slug.ilike(f"%{slug}%"))
        if lon is not None and lat is not None:
            search_radius = 0.01
            stmt = stmt.filter(
                (Constituency.lon.between(lon - search_radius, lon + search_radius)) & 
                (Constituency.lat.between(lat - search_radius, lat + search_radius))
            )
        if region_id is not None:
            stmt = stmt.filter(Constituency.region_id == region_id)
        if district_id is not None:
            stmt = stmt.filter(Constituency.district_id == district_id)
        if created_at:
            stmt = stmt.filter(Constituency.createdAt >= created_at)
        if created_by:
            stmt = stmt.filter(Constituency.createdBy.ilike(f"%{created_by}%"))
        if updated_at:
            stmt = stmt.filter(Constituency.updatedAt >= updated_at)
        if updated_by:
            stmt = stmt.filter(Constituency.updatedBy.ilike(f"%{updated_by}%"))

        # Pagination and sorting
        pagination_params = PaginationParams(skip=skip, limit=limit, sort_field=sort_field, sort_order=sort_order)
        paginated_query = paginate_and_sort(stmt, pagination_params)

        result = db.execute(paginated_query)
        constituencies = result.all()  

        return success_response(data=[{
            **jsonable_encoder(ConstituencyRead.from_orm(constituency[0])),
            "region_name": constituency[1],
            "district_name": constituency[2], 
        } for constituency in constituencies])

    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# CREATE
@router.post("/super/constituencies", response_model=ConstituencyCreate)
def create_constituency(constituency: ConstituencyCreate, db: Session = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.name == constituency.name)
        result =  db.execute(stmt)
        existing_constituency = result.scalar_one_or_none()

        if existing_constituency:
            return error_response(status_code=400, error_message="constituency already exists")
        
        new_data = Constituency(name=constituency.name, lon=constituency.lon, lat=constituency.lat, region_id=constituency.region_id, district_id=constituency.district_id)
        db.add(new_data)
        db.commit()
        db.refresh(new_data)

        return success_response(data=jsonable_encoder(ConstituencyRead.from_orm(new_data)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# UPDATE constituency
@router.put("/super/constituencies/{id}", response_model=ConstituencyRead)
def update_constituency(id: int, constituency_data: ConstituencyUpdate, db: Session = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.id == id)
        result =  db.execute(stmt)
        constituency = result.scalar_one_or_none()

        if not constituency:
            return error_response(status_code=404, error_message="constituency not found")
        
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

# SOFT DELETE CONSTITUENCY
@router.delete("/super/constituencies/{id}")
def soft_delete_constituency(id: int, delete_data: ConstituencySoftDelete, db: Session = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.id == id, Constituency.deleted == False)
        result =  db.execute(stmt)
        constituency = result.scalar_one_or_none()

        if not constituency:
            return error_response(status_code=404, error_message="constituency not found or already deleted")

        constituency.deleted = True
        constituency.deleted_at = datetime.utcnow()
        constituency.deleted_by = "System"
        constituency.deleted_reason = delete_data.deleted_reason

        db.commit()

        return success_response(message="constituency successfully deleted")
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
    
# UPLOAD CONSTITUENCIES
@router.post("/super/constituencies/upload")
def upload_constituencies_csv(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    try:
        df = pd.read_csv(file.file)

        if "name" not in df.columns:
            return error_response(status_code=400, error_message="CSV must contain a 'name' column.")

        processed_constituencies = []

        for _, row in df.iterrows():
            name = row["name"].strip()

            stmt = select(Constituency).filter(Constituency.name == name)
            result =  db.execute(stmt)
            existing_constituency = result.scalars().first()

            if existing_constituency:
                if existing_constituency.active is False and existing_constituency.deleted is True:
                    continue
                existing_constituency.updated_at = datetime.utcnow()
                existing_constituency.updated_by = "System"
            else:
                new_constituency = Constituency(
                    name=name,
                    created_at=datetime.utcnow(),
                    created_by="System",
                    updated_at=datetime.utcnow(),
                    updated_by="System",
                    active=True,
                    deleted=False,
                )
                db.add(new_constituency)
            
            processed_constituencies.append(name)

            db.commit()
        return success_response(
            message=f"CSV processed successfully. Constituency updated/added: {len(processed_constituencies)}",
            data=processed_constituencies,
        )

    except pd.errors.EmptyDataError:
        return error_response(status_code=400, error_message="CSV file is empty.")
    except Exception as e:
        return error_response(status_code=500, error_message=f"Error processing CSV: {str(e)}")

# EXPORT CONSTITUENCIES
@router.post("/super/constituencies/export-csv", response_class=StreamingResponse)
def export_constituencies_csv(db: Session = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.active == True, Constituency.deleted == False)
        result =  db.execute(stmt)
        constituencies = result.scalars().all()

        if not constituencies:
            return error_response(status_code=404, error_message="No constituencies found to export.")

        #define CSV headers
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


