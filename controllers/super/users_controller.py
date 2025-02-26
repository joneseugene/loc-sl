from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
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
def get_users(db: Session = Depends(get_db)):
    try:
        stmt = select(User).filter(User.active == True, User.deleted == False)
        result = db.execute(stmt)
        users = result.scalars().all()
        
        # Serialize object
        user_data = [jsonable_encoder(UserRead.from_orm(user)) for user in users]
        return success_response(data=user_data)
    except Exception as e:
        print("Error fetching users:", e)
        return error_response(status_code=500, error_message=str(e))

