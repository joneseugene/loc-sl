from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query
from utils.consts import USER
from utils.database import get_db
from domain.models.region_model import Region  
from domain.schema.region_schema import RegionRead
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from io import StringIO
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
from utils.pagination_sorting import PaginationParams, paginate_and_sort
import csv


router = APIRouter(tags=["Regions"], dependencies=[Depends(has_role(USER))] )

# FETCH ALL
@router.get("/regions", response_model=List[RegionRead])
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
    lat: Optional[float] = Query(None)
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
  
# EXPORT
@router.post("/regions/export-csv", response_class=StreamingResponse)
def export_regions_csv(db: Session = Depends(get_db)):
    try:
        stmt = select(Region).filter(Region.active == True, Region.deleted == False)
        result = db.execute(stmt)
        regions = result.scalars().all()

        if not regions:
            return error_response(status_code=404, error_message="No regions found to export.")

        # Define CSV headers
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
        # Handle errors and return an appropriate response
        return error_response(status_code=500, error_message=f"Error generating CSV: {str(e)}")

