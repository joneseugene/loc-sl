from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from utils.database import get_db
from domain.models.user_model import User  
from domain.schema.user_schema import UserCreate, UserLogin, UserRead
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder

router = APIRouter(tags=["Users"])

# FETCH ALL
@router.get("/users", response_model=List[UserRead])
async def get_users(db: Session = Depends(get_db)):
    try:
        users = db.query(User).filter(User.active == True, User.deleted == False).all()
        # Serialize each user object
        user_data = [jsonable_encoder(UserRead.from_orm(user)) for user in users]
        
        return success_response(data=user_data)
    except Exception as e:
        print("Error fetching users:", e)
        return error_response(status_code=500, error_message=str(e))

