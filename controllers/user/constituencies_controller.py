from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from domain.models.district_model import District
from domain.models.region_model import Region
from utils.consts import USER
from utils.database import get_db
from domain.models.constituency_model import Constituency 
from domain.schema.constituency_schema import ConstituencyRead
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from io import StringIO
from fastapi.responses import StreamingResponse
from utils.pagination_sorting import PaginationParams, paginate_and_sort
from sqlalchemy.future import select
import csv

router =  APIRouter(tags=["User Constituencies"], dependencies=[Depends(has_role(USER))] )

# FETCH ALL
@router.get("/constituencies", response_model=List[ConstituencyRead])
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
    district_id: Optional[int] = Query(None)
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

# EXPORT
@router.post("/constituencies/export-csv", response_class=StreamingResponse)
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


