from sqlalchemy.orm import Session
from domain.models import User, Role
from domain.schema import UserCreate
from utils.security import hash_password


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = hash_password(user.password)
    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        organization=user.organization,
        password=hashed_password,
        role_id=3  # Default role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user