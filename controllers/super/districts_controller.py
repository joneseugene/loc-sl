from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from domain.models.user_model import User
from utils.security import get_user_from_token
from domain.models.region_model import Region
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
from utils.pagination_sorting import PaginationParams, paginate_and_sort
import pandas as pd
import csv


# router = APIRouter(tags=["Super Districts"], dependencies=[Depends(has_role(SUPER))] )
router = APIRouter(tags=["Super Districts"])

# FETCH ALL
@router.get("/super/districts", response_model=List[DistrictRead])
def get_districts(
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
    created_at: Optional[str] = Query(None),
    created_by: Optional[str] = Query(None),
    updated_at: Optional[str] = Query(None),
    updated_by: Optional[str] = Query(None)
):
    try:
        stmt = select(District, Region.name.label("region_name")).join(Region, District.region_id == Region.id).filter(District.active == True, District.deleted == False)

        # Filters
        if id is not None:
            stmt = stmt.filter(District.id == id)
        if name:
            stmt = stmt.filter(District.name.ilike(f"%{name}%"))
        if slug:
            stmt = stmt.filter(District.slug.ilike(f"%{slug}%"))
        if lon is not None and lat is not None:
            search_radius = 0.01
            stmt = stmt.filter(
                (District.lon.between(lon - search_radius, lon + search_radius)) & 
                (District.lat.between(lat - search_radius, lat + search_radius))
            )
        if region_id is not None:
            stmt = stmt.filter(District.region_id == region_id)
        if created_at:
            stmt = stmt.filter(District.createdAt >= created_at)
        if created_by:
            stmt = stmt.filter(District.createdBy.ilike(f"%{created_by}%"))
        if updated_at:
            stmt = stmt.filter(District.updatedAt >= updated_at)
        if updated_by:
            stmt = stmt.filter(District.updatedBy.ilike(f"%{updated_by}%"))

        # Pagination and sorting
        pagination_params = PaginationParams(skip=skip, limit=limit, sort_field=sort_field, sort_order=sort_order)
        paginated_query = paginate_and_sort(stmt, pagination_params)

        result = db.execute(paginated_query)
        districts = result.all()  

        return success_response(data=[{
            **jsonable_encoder(DistrictRead.from_orm(district[0])),
            "region_name": district[1]  
        } for district in districts])

    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# CREATE
@router.post("/super/districts", response_model=DistrictCreate)
def create_district(
    district: DistrictCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
    ):
    try:
        stmt = select(District).filter(District.name == district.name)
        result = db.execute(stmt)
        existing_district = result.scalars().first()

        if existing_district:
            return error_response(status_code=400, error_message="District already exists")

        new_district = District(
            name=district.name, 
            lon=district.lon, 
            lat=district.lat, 
            region_id=district.region_id,
            created_by=current_user.email,
            updated_by=current_user.email
        )
        db.add(new_district)
        db.commit()
        db.refresh(new_district)
        return success_response(data=jsonable_encoder(DistrictRead.from_orm(new_district)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# UPLOAD
@router.post("/super/districts/upload")
def upload_districts_csv(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
    ):
    try:
        if not file.filename.endswith(".csv"):
            return error_response(status_code=400, error_message="Only CSV files are allowed.")

        df = pd.read_csv(file.file, encoding="utf-8", delimiter=",", header=0)
        print("CSV Columns:", df.columns.tolist())
        df.columns = df.columns.str.strip()
        required_columns = {"no", "name", "lon", "lat", "region_id"}
        if not required_columns.issubset(df.columns):
            return error_response(
                status_code=400,
                error_message=f"Invalid CSV content format. Expected: {list(required_columns)}, but got: {df.columns.tolist()}."
            )

        processed_districts = []

        for _, row in df.iterrows():
            name = row["name"].strip()
            lon = row["lon"]
            lat = row["lat"]
            region_id = row["region_id"]

            # Check if district already exists
            stmt = select(District).filter(District.name == name)
            result = db.execute(stmt)
            existing_district = result.scalars().first()

            if existing_district:
                if existing_district.active is False and existing_district.deleted is True:
                    continue
                existing_district.lon = lon
                existing_district.lat = lat
                existing_district.updated_at = datetime.utcnow()
                existing_district.updated_by = current_user.email
            else:
                new_district = District(
                    name=name,
                    lon=lon,
                    lat=lat,
                    region_id=region_id,
                    created_at=datetime.utcnow(),
                    created_by=current_user.email,
                    updated_at=datetime.utcnow(),
                    updated_by=current_user.email,
                    active=True,
                    deleted=False,
                )
                db.add(new_district)

            processed_districts.append({"name": name, "longitude": lon, "latitude": lat, "region_id": region_id})

        db.commit()
        return success_response(
            message=f"CSV processed successfully. District(s) updated/added: {len(processed_districts)}",
            data=processed_districts,
        )

    except pd.errors.EmptyDataError:
        return error_response(status_code=400, error_message="CSV file is empty.")
    except Exception as e:
        return error_response(status_code=500, error_message=f"Error processing CSV: {str(e)}")

# UPDATE
@router.put("/super/districts/{id}", response_model=DistrictRead)
def update_district(
    id: int, 
    district_data: DistrictUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
    ):
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
        district.updated_by = current_user.email

        db.commit()
        db.refresh(district)

        return success_response(data=jsonable_encoder(DistrictRead.from_orm(district)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# EXPORT
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

# SOFT DELETE
@router.delete("/super/districts/{id}")
def soft_delete_district(
    id: int, 
    delete_data: DistrictSoftDelete, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
    ):
    try:
        stmt = select(District).filter(District.id == id, District.deleted == False)
        result = db.execute(stmt)
        district = result.scalars().first()

        if not district:
            return error_response(status_code=404, error_message="District not found or already deleted")

        district.deleted = True
        district.deleted_at = datetime.utcnow()
        district.deleted_by = current_user.email
        district.deleted_reason = delete_data.deleted_reason

        db.commit()
        return success_response(message="District successfully deleted")
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
