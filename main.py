from fastapi import FastAPI
from controllers.super.users_controller import router as users_router  
from controllers.super.regions_controller import router as regions_router  
from controllers.super.districts_controller import router as districts_router  
from controllers.super.roles_controller import router as roles_router  
from controllers.auth_controller import router as auth_router  
from middlewares.exception_handling_middleware import register_exception_handlers
from middlewares.rate_limiter_middleware import rate_limit_middleware
import redis
from fastapi_limiter import FastAPILimiter

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


# Routes
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(regions_router, prefix="/api")
app.include_router(districts_router, prefix="/api")
app.include_router(roles_router, prefix="/api")
