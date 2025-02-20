from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from utils.database import get_db
from domain.models.constituency_model import Constituency 
from domain.schema.constituency_schema import ConstituencyCreate, ConstituencyRead, ConstituencySoftDelete, ConstituencyUpdate
from utils.functions import has_role
from utils.http_response import success_response, error_response
from fastapi.encoders import jsonable_encoder
import pandas as pd
import csv
from io import StringIO
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router =  APIRouter(tags=["Super Constituencies"], dependencies=[Depends(has_role(1))] )

# FETCH ALL
@router.get("/super/constituencies", response_model=List[ConstituencyRead])
async def get_constituencies(db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.active == True, Constituency.deleted == False)
        result = await db.execute(stmt)
        constituencies = result.scalars().all()

        # Serialize object
        constituency_data = [jsonable_encoder(ConstituencyRead.from_orm(constituency)) for constituency in constituencies]
        return success_response(data=constituency_data)
    except Exception as e:
        print("Error fetching constituencies:", e)
        return error_response(status_code=500, error_message=str(e))

# FIND BY ID
@router.get("/super/constituencies/{id}", response_model=ConstituencyRead)
async def get_constituency_by_id(id: int, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.id == id, Constituency.active == True, Constituency.deleted == False)
        result = await db.execute(stmt)
        constituency = result.scalar_one_or_none()

        if not constituency:
            return error_response(status_code=404, error_message="constituency not found")
        
        return success_response(data=jsonable_encoder(ConstituencyRead.from_orm(constituency)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY CONSTITUENCY ID
@router.get("/super/constituencies/constituency/{constituencyn_id}", response_model=List[ConstituencyRead])
async def get_constituency_by_constituency_id(constituency_id: int, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.constituency_id == constituency_id, Constituency.active == True, Constituency.deleted == False)
        result = await db.execute(stmt)
        constituencies = result.scalars().all()

        if not constituencies:
            return error_response(status_code=404, error_message="constituency not found")
        
        return success_response(data=jsonable_encoder([ConstituencyRead.from_orm(constituency) for constituency in constituencies]))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY DISTRICT ID
@router.get("/super/constituencies/district/{district_id}", response_model=List[ConstituencyRead])
async def get_constituency_by_district_id(district_id: int, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.district_id == district_id, Constituency.active == True, Constituency.deleted == False)
        result = await db.execute(stmt)
        constituencies = result.scalars().all()

        if not constituencies:
            return error_response(status_code=404, error_message="constituency not found")
        
        return success_response(data=jsonable_encoder([ConstituencyRead.from_orm(constituency) for constituency in constituencies]))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# FIND BY NAME
@router.get("/super/constituencies/name/{name}", response_model=ConstituencyRead)
async def get_constituency_by_name(name: str, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.name == name, Constituency.active == True, Constituency.deleted == False)
        result = await db.execute(stmt)
        constituency = result.scalar_one_or_none()

        if not constituency:
            return error_response(status_code=404, error_message="constituency not found")
        
        return success_response(data=jsonable_encoder(ConstituencyRead.from_orm(constituency)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# CREATE
@router.post("/super/constituencies", response_model=ConstituencyCreate)
async def create_constituency(constituency: ConstituencyCreate, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.name == constituency.name)
        result = await db.execute(stmt)
        existing_constituency = result.scalar_one_or_none()

        if existing_constituency:
            return error_response(status_code=400, error_message="constituency already exists")
        
        new_data = Constituency(name=constituency.name, lon=constituency.lon, lat=constituency.lat, constituency_id=constituency.constituency_id)
        db.add(new_data)
        await db.commit()
        await db.refresh(new_data)

        return success_response(data=jsonable_encoder(ConstituencyRead.from_orm(new_data)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# UPDATE constituency
@router.put("/super/constituencies/{id}", response_model=ConstituencyRead)
async def update_constituency(id: int, constituency_data: ConstituencyUpdate, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.id == id)
        result = await db.execute(stmt)
        constituency = result.scalar_one_or_none()

        if not constituency:
            return error_response(status_code=404, error_message="constituency not found")
        
        update_data = constituency_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(constituency, key, value)

        constituency.updated_at = datetime.utcnow()
        constituency.updated_by = "System"

        await db.commit()
        await db.refresh(constituency)

        return success_response(data=jsonable_encoder(ConstituencyRead.from_orm(constituency)))
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))


# SOFT DELETE constituency
@router.delete("/super/constituencies/{id}")
async def soft_delete_constituency(id: int, delete_data: ConstituencySoftDelete, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.id == id, Constituency.deleted == False)
        result = await db.execute(stmt)
        constituency = result.scalar_one_or_none()

        if not constituency:
            return error_response(status_code=404, error_message="constituency not found or already deleted")

        constituency.deleted = True
        constituency.deleted_at = datetime.utcnow()
        constituency.deleted_by = "System"
        constituency.deleted_reason = delete_data.deleted_reason

        await db.commit()

        return success_response(message="constituency successfully deleted")
    except Exception as e:
        return error_response(status_code=500, error_message=str(e))
    

# UPLOAD CONSTITUENCIES
@router.post("/super/constituencies/upload")
async def upload_onstituencies_csv(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    try:
        df = pd.read_csv(file.file)

        if "name" not in df.columns:
            return error_response(status_code=400, error_message="CSV must contain a 'name' column.")

        processed_constituencies = []

        for _, row in df.iterrows():
            name = row["name"].strip()

            stmt = select(Constituency).filter(Constituency.name == name)
            result = await db.execute(stmt)
            existing_constituency = result.scalars().first()

            if existing_constituency:
                if existing_constituency.active is False and existing_constituency.deleted is True:
                    continue
                existing_constituency.updated_at = datetime.utcnow()
                existing_constituency.updated_by = "System"
            else:
                new_constituency = Constituency(
                    name=name,
                    created_at=datetime.utcnow(),
                    created_by="System",
                    updated_at=datetime.utcnow(),
                    updated_by="System",
                    active=True,
                    deleted=False,
                )
                db.add(new_constituency)
            
            processed_constituencies.append(name)

        await db.commit()
        return success_response(
            message=f"CSV processed successfully. Constituency updated/added: {len(processed_constituencies)}",
            data=processed_constituencies,
        )

    except pd.errors.EmptyDataError:
        return error_response(status_code=400, error_message="CSV file is empty.")
    except Exception as e:
        return error_response(status_code=500, error_message=f"Error processing CSV: {str(e)}")



@router.post("/super/constituencies/export-csv", response_class=StreamingResponse)
async def export_constituencies_csv(db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Constituency).filter(Constituency.active == True, Constituency.deleted == False)
        result = await db.execute(stmt)
        constituencies = result.scalars().all()

        if not constituencies:
            return error_response(status_code=404, error_message="No constituencies found to export.")

        # Define CSV headers
        csv_headers = ["No", "Name", "Slug", "Longitude", "Latitude"]

        # Create a StringIO object to hold the CSV data
        csv_data = StringIO()
        csv_writer = csv.writer(csv_data)

        # Write the headers to the CSV
        csv_writer.writerow(csv_headers)

        # Add the row number (No) and data for each constituency
        for idx, constituency in enumerate(constituencies, start=1):  # start=1 to begin the "No" column at 1
            csv_writer.writerow([
                idx,  # Row number (No)
                constituency.name,
                constituency.slug,
                constituency.lon,
                constituency.lat,
            ])

        # Rewind the StringIO object to the beginning for streaming
        csv_data.seek(0)

        # Return the CSV data as a streaming response
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


