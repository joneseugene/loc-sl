from fastapi import FastAPI
from controllers.auth_controller import router as auth_router  
# Super Routes
from controllers.super.users_controller import router as users_router  
from controllers.super.roles_controller import router as roles_router  
from controllers.super.regions_controller import router as super_region_router  
from controllers.super.districts_controller import router as super_district_router  
from controllers.super.constituencies_controller import router as super_constituency_router  
from controllers.super.wards_controller import router as super_ward_router  
# Admin Routes
from controllers.admin.regions_controller import router as admin_region_router  
from controllers.admin.districts_controller import router as admin_district_router  
from controllers.admin.constituencies_controller import router as admin_constituency_router  
from controllers.admin.wards_controller import router as admin_ward_router  
# User Routes
from controllers.user.regions_controller import router as user_region_router  
from controllers.user.districts_controller import router as user_district_router  
from controllers.user.constituencies_controller import router as user_constituency_router  
from controllers.user.wards_controller import router as user_ward_router  
# Middlewares
from middlewares.exception_handling_middleware import register_exception_handlers
from middlewares.rate_limiter_middleware import rate_limit_middleware

# Initialization
app = FastAPI(
    title="Sierra Leone Locations API",
    description="API developed by DSTI to provide a structured data on locations in Sierra Leone.",
    version="1.0.0",
    docs_url="/docs",  
    redoc_url="/redoc",  
)

# Middlewares
app.middleware("http")(rate_limit_middleware)

register_exception_handlers(app)


# Routes for Super
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(roles_router, prefix="/api")
app.include_router(super_region_router, prefix="/api")
app.include_router(super_district_router, prefix="/api")
app.include_router(super_constituency_router, prefix="/api")
app.include_router(super_ward_router, prefix="/api")
# Routes for Admins
app.include_router(admin_region_router, prefix="/api")
app.include_router(admin_district_router, prefix="/api")
app.include_router(admin_constituency_router, prefix="/api")
app.include_router(admin_ward_router, prefix="/api")
# Routes for Users
app.include_router(user_region_router, prefix="/api")
app.include_router(user_district_router, prefix="/api")
app.include_router(user_constituency_router, prefix="/api")
app.include_router(user_ward_router, prefix="/api")
