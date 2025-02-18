from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Environment variables
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
HASHING_ALGORITHM = os.getenv("HASHING_ALGORITHM")
ACCESS_TOKEN_EXPIRY_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRY_MINUTES")
ENCRYPTION = os.getenv("ENCRYPTION")

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
