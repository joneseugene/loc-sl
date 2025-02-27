# Run app
python -m uvicorn main:app --reload


# DEPENDENCIES
# Install FastAPI and Uvicorn
pip install fastapi uvicorn

# Install Database Dependencies
pip install sqlalchemy asyncpg alembic

# Install Pydantic for validation
pip install pydantic

# Install JWT Authentication
pip install python-jose[cryptography] passlib bcrypt python-multipart
pip install pydantic[email]
pip install pyjwt

# Install Dotenv
pip install python-dotenv

# Install for Migrations
pip install alembic

# Request Limiter
pip install setuptools
pip install fastapi-limiter aioredis

# Slugify
pip install python-slugify

# Pandas
pip install pandas

# Install from requirements.txt
pip install -r requirements.txt

# Track Locations
pip install geopy



# MIGRATIONS
# Initialize Alembic
python -m alembic init migrations

# Generate migration for models
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head

