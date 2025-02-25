from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from domain.models.region_model import Region
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
from utils.pagination_sorting import PaginationParams, paginate_and_sort
import csv


router = APIRouter(tags=["Districts"], dependencies=[Depends(has_role(USER))] )

# FETCH ALL
@router.get("/districts", response_model=List[DistrictRead])
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
    region_id: Optional[int] = Query(None)
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


# EXPORT
@router.post("/districts/export-csv", response_class=StreamingResponse)
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
