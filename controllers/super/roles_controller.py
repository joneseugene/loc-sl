from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.future import select 
from utils.consts import SUPER
from utils.database import get_db
from domain.models.role_model import Role 
from domain.schema.role_schema import RoleCreate, RoleRead, RoleSoftDelete, RoleUpdate
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder

router = APIRouter(tags=["Super Roles"], dependencies=[Depends(has_role(SUPER))])

# FETCH ALL
@router.get("/super/roles", response_model=List[RoleRead])
def get_roles(db: Session = Depends(get_db)):  
    try:
        stmt = select(Role).filter(Role.active == True, Role.deleted == False)
        result = db.execute(stmt)
        roles = result.scalars().all()
        
        # Serialize object
        role_data = [jsonable_encoder(RoleRead.from_orm(role)) for role in roles]
        return success_response(data=role_data)
    except Exception as e:
        print("Error fetching roles:", e)
        return error_response(status_code=500, error_message=str(e))


# FIND BY ID
@router.get("/super/roles/{id}", response_model=RoleRead)
def get_role_by_id(id: int, db: Session = Depends(get_db)): 
    try:
        stmt = select(Role).filter(Role.id == id, Role.active == True, Role.deleted == False)
        result = db.execute(stmt)
        role = result.scalars().first()
        if not role:
            return error_response(status_code=404, error_message="role not found")
        return success_response(data=jsonable_encoder(RoleRead.from_orm(role)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY NAME
@router.get("/super/roles/name/{name}", response_model=RoleRead)
def get_role_by_name(name: str, db: Session = Depends(get_db)):  
    try:
        stmt = select(Role).filter(Role.name == name, Role.active == True, Role.deleted == False)
        result = db.execute(stmt)
        role = result.scalars().first()
        if not role:
            return error_response(status_code=404, error_message="role not found")
        return success_response(data=jsonable_encoder(RoleRead.from_orm(role)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
    
    
# CREATE
@router.post("/super/roles", response_model=RoleRead)  # Changed RoleCreate → RoleRead
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    try:
        # Check if the role already exists
        query = select(Role).filter(Role.name == role.name)
        result = db.execute(query)
        existing_role = result.scalars().first()

        if existing_role:
            return error_response(status_code=400, error_message="role already exists")

        # Create a new role
        new_role = Role(name=role.name)
        db.add(new_role)
        db.commit()  
        db.refresh(new_role)
        
        return success_response(data=jsonable_encoder(RoleRead.from_orm(new_role)))
    except Exception as e:
        print(f"Error creating role: {e}")
        return error_response(status_code=500, error_message=str(e))


# UPDATE
@router.put("/super/roles/{id}", response_model=RoleRead)
def update_role(id: int, role_data: RoleUpdate, db: Session = Depends(get_db)):
    try:
        query = select(Role).filter(Role.id == id)
        result = db.execute(query)
        role = result.scalars().first()

        if not role:
            return error_response(status_code=404, error_message="role not found")
        
        # Update only provided fields
        update_data = role_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(role, key, value)

        role.updated_at = datetime.utcnow()
        role.updated_by = "System"

        db.commit()
        db.refresh(role)

        return success_response(data=jsonable_encoder(RoleRead.from_orm(role)))
    except Exception as e:
        print(f"Error updating role ID {id}: {e}")
        return error_response(status_code=500, error_message=str(e))


# SOFT DELETE
@router.delete("/super/roles/{id}")
def soft_delete_role(id: int, delete_data: RoleSoftDelete, db: Session = Depends(get_db)):
    try:
        query = select(Role).filter(Role.id == id, Role.deleted == False)
        result = db.execute(query)
        role = result.scalars().first()

        if not role:
            return error_response(status_code=404, error_message="role not found or already deleted")

        # Soft delete role
        role.deleted = True
        role.deleted_at = datetime.utcnow()
        role.deleted_by = "System"
        role.deleted_reason = delete_data.deleted_reason

        db.commit()
        return success_response(message="role successfully deleted", data=None)  
    except Exception as e:
        print(f"Error soft deleting role ID {id}: {e}")
        return error_response(status_code=500, error_message=str(e))