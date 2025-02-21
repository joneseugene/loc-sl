from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.future import select 
from utils.consts import USER
from utils.database import get_db
from domain.models.user_model import User  
from domain.schema.user_schema import UserCreate, UserLogin, UserRead
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
from utils.security import hash_password, verify_password, create_access_token

router = APIRouter(tags=["Auth"])


# REGISTER
@router.post("/register", response_model=UserRead)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        result = db.execute(select(User).filter(User.email == user.email))
        db_user = result.scalars().first()  

        if db_user:
            return error_response(status_code=400, error_message="user already exists")

        hashed_password = hash_password(user.password)
        new_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            organization=user.organization,
            password=hashed_password,
            role_id=USER,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return success_response(
            data=jsonable_encoder(UserRead.from_orm(new_user)),
            message="user registered successfully"
        )
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
 
    
# LOGIN
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    try:
        result = db.execute(select(User).filter(User.email == user.email))
        db_user = result.scalars().first()  

        if not db_user or not verify_password(user.password, db_user.password):
            return error_response(status_code=400, error_message="invalid email or password")

        # Token Info
        access_token, expiry_time = create_access_token(data={
            "sub": db_user.email,
            "first_name": db_user.first_name,
            "last_name": db_user.last_name,
            "organization": db_user.organization
        })

        return success_response(
            data={
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_at": expiry_time.isoformat()
            },
            message="authentication successful"
        )
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
