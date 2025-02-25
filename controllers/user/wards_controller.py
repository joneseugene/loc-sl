from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from domain.models.constituency_model import Constituency
from domain.models.district_model import District
from domain.models.region_model import Region
from utils.consts import USER
from utils.database import get_db
from domain.models.ward_model import Ward
from domain.schema.ward_schema import WardRead
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from io import StringIO
from fastapi.responses import StreamingResponse
from utils.pagination_sorting import PaginationParams, paginate_and_sort
from sqlalchemy.future import select
import csv

router = APIRouter(tags=["User Wards"], dependencies=[Depends(has_role(USER))])

# FETCH ALL
@router.get("/wards", response_model=List[WardRead])
def get_wards(
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
    constituency_id: Optional[int] = Query(None)
):
    try:
        stmt = select(
            Ward,
            Region.name.label("region_name"),
            District.name.label("district_name"),
            Constituency.name.label("constituency_name")
        ).join(Region, Ward.region_id == Region.id
        ).join(District, Ward.district_id == District.id
        ).join(Constituency, Ward.constituency_id == Constituency.id
        ).filter(Ward.active == True, Ward.deleted == False)

        # Filters
        if id is not None:
            stmt = stmt.filter(Ward.id == id)
        if name:
            stmt = stmt.filter(Ward.name.ilike(f"%{name}%"))
        if slug:
            stmt = stmt.filter(Ward.slug.ilike(f"%{slug}%"))
        if lon is not None and lat is not None:
            search_radius = 0.01
            stmt = stmt.filter(
                (Ward.lon.between(lon - search_radius, lon + search_radius)) & 
                (Ward.lat.between(lat - search_radius, lat + search_radius))
            )
        if region_id is not None:
            stmt = stmt.filter(Ward.region_id == region_id)
        if district_id is not None:
            stmt = stmt.filter(Ward.district_id == district_id)
        if constituency_id is not None:
            stmt = stmt.filter(Ward.district_id == district_id)

        # Pagination and sorting
        pagination_params = PaginationParams(skip=skip, limit=limit, sort_field=sort_field, sort_order=sort_order)
        paginated_query = paginate_and_sort(stmt, pagination_params)

        result = db.execute(paginated_query)
        wards = result.all()  

        return success_response(data=[{
            **jsonable_encoder(WardRead.from_orm(ward[0])),
            "region_name": ward[1],
            "district_name": ward[2], 
            "constituency_name": ward[3], 
        } for ward in wards])

    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# EXPORT
@router.post("/wards/export-csv", response_class=StreamingResponse)
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
