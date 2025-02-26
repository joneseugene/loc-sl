from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from domain.models.chiefdom_model import Chiefdom
from domain.models.district_model import District
from domain.models.region_model import Region
from domain.schema.chiefdom_schema import ChiefdomRead
from utils.consts import SUPER
from utils.database import get_db
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from io import StringIO
from utils.pagination_sorting import PaginationParams, paginate_and_sort
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
import pandas as pd
import csv


#router =  APIRouter(tags=["Chiefdoms"], dependencies=[Depends(has_role(SUPER))] )
router =  APIRouter(tags=["Chiefdoms"])

# FETCH ALL
@router.get("/chiefdoms", response_model=List[ChiefdomRead])
def get_chiefdoms(
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
            Chiefdom,
            Region.name.label("region_name"),
            District.name.label("district_name")
        ).join(Region, Chiefdom.region_id == Region.id
        ).join(District, Chiefdom.district_id == District.id
        ).filter(Chiefdom.active == True, Chiefdom.deleted == False)

        # Filters
        if id is not None:
            stmt = stmt.filter(Chiefdom.id == id)
        if name:
            stmt = stmt.filter(Chiefdom.name.ilike(f"%{name}%"))
        if slug:
            stmt = stmt.filter(Chiefdom.slug.ilike(f"%{slug}%"))
        if lon is not None and lat is not None:
            search_radius = 0.01
            stmt = stmt.filter(
                (Chiefdom.lon.between(lon - search_radius, lon + search_radius)) & 
                (Chiefdom.lat.between(lat - search_radius, lat + search_radius))
            )
        if region_id is not None:
            stmt = stmt.filter(Chiefdom.region_id == region_id)
        if district_id is not None:
            stmt = stmt.filter(Chiefdom.district_id == district_id)
        if created_at:
            stmt = stmt.filter(Chiefdom.createdAt >= created_at)
        if created_by:
            stmt = stmt.filter(Chiefdom.createdBy.ilike(f"%{created_by}%"))
        if updated_at:
            stmt = stmt.filter(Chiefdom.updatedAt >= updated_at)
        if updated_by:
            stmt = stmt.filter(Chiefdom.updatedBy.ilike(f"%{updated_by}%"))

        # Pagination and sorting
        pagination_params = PaginationParams(skip=skip, limit=limit, sort_field=sort_field, sort_order=sort_order)
        paginated_query = paginate_and_sort(stmt, pagination_params)

        result = db.execute(paginated_query)
        chiefdoms = result.all()  

        return success_response(data=[{
            **jsonable_encoder(ChiefdomRead.from_orm(chiefdom[0])),
            "region_name": chiefdom[1],
            "district_name": chiefdom[2], 
        } for chiefdom in chiefdoms])

    except Exception as e:
        return error_response(status_code=500, error_message=str(e))

# EXPORT
@router.post("/chiefdoms/export-csv", response_class=StreamingResponse)
def export_chiefdoms_csv(db: Session = Depends(get_db)):
    try:
        stmt = select(Chiefdom).filter(Chiefdom.active == True, Chiefdom.deleted == False)
        result =  db.execute(stmt)
        chiefdoms = result.scalars().all()

        if not chiefdoms:
            return error_response(status_code=404, error_message="No chiefdom found to export.")

        #define CSV headers
        csv_headers = ["No", "Name", "Slug", "Longitude", "Latitude", "RegionId", "DistrictId"]

        csv_data = StringIO()
        csv_writer = csv.writer(csv_data)

        csv_writer.writerow(csv_headers)

        for idx, chiefdom in enumerate(chiefdoms, start=1):  
            csv_writer.writerow([
                idx,
                chiefdom.name,
                chiefdom.slug,
                chiefdom.lon,
                chiefdom.lat,
                chiefdom.region_id,
                chiefdom.district_id,
            ])

        csv_data.seek(0)

        return StreamingResponse(
            iter([csv_data.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=chiefdoms.csv",
                "Content-Length": str(len(csv_data.getvalue())),
            }
        )

    except Exception as e:
        return error_response(status_code=500, error_message=f"Error generating CSV: {str(e)}")


