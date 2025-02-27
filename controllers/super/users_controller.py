from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from domain.models.user_model import User
from utils.pagination_sorting import PaginationParams, paginate_and_sort
from utils.security import get_user_from_token
from utils.consts import SUPER
from utils.database import get_db
from domain.models.user_model import User  
from domain.schema.user_schema import UserRead
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.future import select

router = APIRouter(tags=["Super Users"], dependencies=[Depends(has_role(SUPER))] )

# FETCH ALL
@router.get("/super/users", response_model=List[UserRead])
def get_roles(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),  
    limit: int = Query(10, ge=1, le=100),  
    sort_field: Optional[str] = Query(None),
    sort_order: Optional[str] = Query("asc"),
    id: Optional[int] = Query(None),
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    organization: Optional[str] = Query(None),
    role_id: Optional[int] = Query(None),
    created_at: Optional[str] = Query(None),
    created_by: Optional[str] = Query(None),
    updated_at: Optional[str] = Query(None),
    updated_by: Optional[str] = Query(None)
    ):
    try:
        stmt = select(User).filter(User.active == True, User.deleted == False)

        # Filters
        if id is not None:
            stmt = stmt.filter(User.id == id)
        if first_name:
            stmt = stmt.filter(User.first_name.ilike(f"%{first_name}%"))
        if last_name:
            stmt = stmt.filter(User.last_name.ilike(f"%{last_name}%"))
        if email:
            stmt = stmt.filter(User.email.ilike(f"%{email}%"))
        if organization:
            stmt = stmt.filter(User.organization.ilike(f"%{organization}%"))
        if role_id is not None:
            stmt = stmt.filter(User.role_id == role_id)
        if created_at:
            stmt = stmt.filter(User.createdAt >= created_at)
        if created_by:
            stmt = stmt.filter(User.createdBy.ilike(f"%{created_by}%"))
        if updated_at:
            stmt = stmt.filter(User.updatedAt >= updated_at)
        if updated_by:
            stmt = stmt.filter(User.updatedBy.ilike(f"%{updated_by}%"))

        # Pagination and sorting
        pagination_params = PaginationParams(skip=skip, limit=limit, sort_field=sort_field, sort_order=sort_order)
        paginated_query = paginate_and_sort(stmt, pagination_params)

        result = db.execute(paginated_query)
        roles = result.scalars().all()

        # Serialized Response
        return success_response(data=[jsonable_encoder(UserRead.from_orm(role)) for role in roles])

    except Exception as e:
        print("Error fetching roles:", e)
        return error_response(status_code=500, error_message=str(e))

