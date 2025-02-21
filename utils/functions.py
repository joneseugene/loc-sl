from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from slugify import slugify
from domain.models.user_model import User
from domain.schema.user_schema import UserCreate
from utils.consts import USER
from utils.http_response import error_response
from utils.security import get_user_from_token, hash_password


# Get User by email
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# Create User
def create_user(db: Session, user: UserCreate):
    hashed_password = hash_password(user.password)
    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        organization=user.organization,
        password=hashed_password,
        role_id=USER  # Default role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Check User Role
def has_role(role_id: int):
    def role_checker(user: User = Depends(get_user_from_token)):
        if user.role_id != role_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return role_checker

# Automatically generate slug before insert or update
def generate_slug(mapper, connection, target):
    if target.name:
        target.slug = slugify(target.name)

