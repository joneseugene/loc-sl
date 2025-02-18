from fastapi import FastAPI
from controllers.super.users_controller import router as users_router  
from controllers.super.regions_controller import router as regions_router  
from controllers.super.districts_controller import router as districts_router  
from controllers.super.roles_controller import router as roles_router  
from controllers.auth_controller import router as auth_router  
from middlewares.exception_handling_middleware import register_exception_handlers
from middlewares.prevent_ddos_middleware import rate_limiter_middleware
from middlewares.rate_limiter_middleware import init_rate_limiter
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
@app.on_event("startup")
# Initialize REDIS
def startup():
    def init_rate_limiter():
        try:
            my_redis = redis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)
            # Test Redis connection
            my_redis.ping()  
            FastAPILimiter.init(my_redis) 
            print("Rate limiter initialized successfully.")
            app.middleware("http")(rate_limiter_middleware)
        except Exception as e:
            print(f"Error during startup: {e}")
    
register_exception_handlers(app)


# Routes
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(regions_router, prefix="/api")
app.include_router(districts_router, prefix="/api")
app.include_router(roles_router, prefix="/api")
