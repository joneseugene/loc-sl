from typing import Any
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from domain.models.user_model import User
from utils.database import get_db
from dotenv import load_dotenv
import jwt
import os

# Environment variables
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
HASHING_ALGORITHM = os.getenv("HASHING_ALGORITHM")
ACCESS_TOKEN_EXPIRY_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRY_MINUTES")
ENCRYPTION = os.getenv("ENCRYPTION")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=[ENCRYPTION], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expiry_minutes = expires_delta or timedelta(minutes=int(ACCESS_TOKEN_EXPIRY_MINUTES))
    expire = datetime.utcnow() + expiry_minutes
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=HASHING_ALGORITHM)
    return token, expire

def decode_jwt(token: str) -> Any:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[HASHING_ALGORITHM])
        return payload 
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def get_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_jwt(token)
    email_value = payload.get("sub") # Extract the sub field
    user = db.query(User).filter(User.email == email_value).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

