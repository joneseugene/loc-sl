from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from domain.models.user_model import User
from utils.security import get_user_from_token
from utils.consts import SUPER
from utils.database import get_db
from domain.models.region_model import Region  
from domain.schema.region_schema import RegionCreate, RegionRead, RegionSoftDelete, RegionUpdate
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from io import StringIO
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
from utils.pagination_sorting import PaginationParams, paginate_and_sort
import pandas as pd
import csv


# router = APIRouter(tags=["Super Regions"], dependencies=[Depends(has_role(SUPER))] )
router = APIRouter(tags=["Super Regions"])

# FETCH ALL
@router.get("/super/regions", response_model=List[RegionRead])
def get_regions(
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
    created_at: Optional[str] = Query(None),
    created_by: Optional[str] = Query(None),
    updated_at: Optional[str] = Query(None),
    updated_by: Optional[str] = Query(None)
):
    try:
        stmt = select(Region).filter(Region.active == True, Region.deleted == False)

        # Filters
        if id is not None:
            stmt = stmt.filter(Region.id == id)
        if name:
            stmt = stmt.filter(Region.name.ilike(f"%{name}%"))
        if slug:
            stmt = stmt.filter(Region.slug.ilike(f"%{slug}%"))
        if lon is not None and lat is not None:
            search_radius = 0.01
            stmt = stmt.filter(
                (Region.lon.between(lon - search_radius, lon + search_radius)) &
                (Region.lat.between(lat - search_radius, lat + search_radius))
            )
        if created_at:
            stmt = stmt.filter(Region.createdAt >= created_at)
        if created_by:
            stmt = stmt.filter(Region.createdBy.ilike(f"%{created_by}%"))
        if updated_at:
            stmt = stmt.filter(Region.updatedAt >= updated_at)
        if updated_by:
            stmt = stmt.filter(Region.updatedBy.ilike(f"%{updated_by}%"))

        # Pagination and sorting
        pagination_params = PaginationParams(skip=skip, limit=limit, sort_field=sort_field, sort_order=sort_order)
        paginated_query = paginate_and_sort(stmt, pagination_params)

        result = db.execute(paginated_query)
        regions = result.scalars().all()

        # Serialized Response
        return success_response(data=[jsonable_encoder(RegionRead.from_orm(region)) for region in regions])

    except Exception as e:
        print("Error fetching regions:", e)
        return error_response(status_code=500, error_message=str(e))
    
# CREATE
@router.post("/super/regions", response_model=RegionCreate)
def create_region(
    region: RegionCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_user_from_token)):
    try:
        stmt = select(Region).filter(Region.name == region.name)
        result = db.execute(stmt)
        existing_region = result.scalars().first()
        
        if existing_region:
            return error_response(status_code=400, error_message="Region already exists")

        new_region = Region(
            name=region.name, 
            lon=region.lon, 
            lat=region.lat, 
            created_by=current_user.email,
            updated_by=current_user.email
        )
        db.add(new_region)
        db.commit()
        db.refresh(new_region)
        
        return success_response(data=jsonable_encoder(RegionRead.from_orm(new_region)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# UPLOAD
@router.post("/super/regions/upload")
def upload_regions_csv(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
    ):
    try:
        if not file.filename.endswith(".csv"):
            return error_response(status_code=400, error_message="Only CSV files are allowed.")
        
        if file.filename != "regions.csv":
            return error_response(status_code=400, error_message="File must be named 'regions.csv'.")

        df = pd.read_csv(file.file, encoding="utf-8", delimiter=",", header=0)
        print("CSV Columns:", df.columns.tolist())
        df.columns = df.columns.str.strip()
        required_columns = {"no", "name", "lon", "lat"}
        if not required_columns.issubset(df.columns):
            return error_response(
                status_code=400,
                error_message=f"Invalid CSV content format. Expected: {list(required_columns)}, but got: {df.columns.tolist()}."
            )

        processed_regions = []

        for _, row in df.iterrows():
            name = row["name"].strip()
            lon = row["lon"]
            lat = row["lat"]

            # Check if region already exists
            stmt = select(Region).filter(Region.name == name)
            result = db.execute(stmt)
            existing_region = result.scalars().first()

            if existing_region:
                if existing_region.active is False and existing_region.deleted is True:
                    continue
                existing_region.lon = lon
                existing_region.lat = lat
                existing_region.updated_at = datetime.utcnow()
                existing_region.updated_by = current_user.email
            else:
                new_region = Region(
                    name=name,
                    lon=lon,
                    lat=lat,
                    created_at=datetime.utcnow(),
                    created_by=current_user.email,
                    updated_at=datetime.utcnow(),
                    updated_by=current_user.email,
                    active=True,
                    deleted=False,
                )
                db.add(new_region)

            processed_regions.append({"name": name, "longitude": lon, "latitude": lat})
        db.commit()
        return success_response(
            message=f"CSV processed successfully. Region(s) updated/added: {len(processed_regions)}",
            data=processed_regions,
        )
    except pd.errors.EmptyDataError:
        return error_response(status_code=400, error_message="CSV file is empty.")
    except Exception as e:
        return error_response(status_code=500, error_message=f"Error processing CSV: {str(e)}")

# EXPORT
@router.post("/super/regions/export-csv", response_class=StreamingResponse)
def export_regions_csv(db: Session = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.active == True, Region.deleted == False)
        result = db.execute(stmt)
        regions = result.scalars().all()

        if not regions:
            return error_response(status_code=404, error_message="No regions found to export.")

        # CSV headers
        csv_headers = ["No", "Name", "Slug", "Longitude", "Latitude"]

        csv_data = StringIO()
        csv_writer = csv.writer(csv_data)
        csv_writer.writerow(csv_headers)

        for idx, region in enumerate(regions, start=1): 
            csv_writer.writerow([
                idx, 
                region.name,
                region.slug,
                region.lon,
                region.lat,
            ])

        csv_data.seek(0)

        return StreamingResponse(
            iter([csv_data.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=regions.csv",
                "Content-Length": str(len(csv_data.getvalue())),
            }
        )

    except Exception as e:
        return error_response(status_code=500, error_message=f"Error generating CSV: {str(e)}")

# UPDATE
@router.put("/super/regions/{id}", response_model=RegionRead)
def update_region(
    id: int, 
    region_data: RegionUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
    ):
    try:
        stmt = select(Region).filter(Region.id == id)
        result = db.execute(stmt)
        region = result.scalars().first()
        
        if not region:
            return error_response(status_code=404, error_message="Region not found")

        update_data = region_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(region, key, value)
            region.updated_at = datetime.utcnow()
            region.updated_by = current_user.email

        db.commit()
        db.refresh(region)
        
        return success_response(data=jsonable_encoder(RegionRead.from_orm(region)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# SOFT DELETE
@router.delete("/super/regions/{id}")
def soft_delete_region(
    id: int, 
    delete_data: RegionSoftDelete, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
    ):
    try:
        stmt = select(Region).filter(Region.id == id, Region.deleted == False)
        result = db.execute(stmt)
        region = result.scalars().first()

        if not region:
            return error_response(status_code=404, error_message="Region not found or already deleted")

        region.deleted = True
        region.deleted_at = datetime.utcnow()
        region.deleted_by = current_user.email
        region.deleted_reason = delete_data.deleted_reason

        db.commit()
        return success_response(message="Region successfully deleted")
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
    