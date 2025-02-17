from fastapi import FastAPI
from controllers.regions import router as regions_router  
from utils.exception_handlers import register_exception_handlers


app = FastAPI(
    title="Sierra Leone Locations API",
    description="API developed by DSTI to provide a structured data on locations in Sierra Leone.",
    version="1.0.0",
    docs_url="/docs",  
    redoc_url="/redoc",  
)

# Exception Handling Middleware
register_exception_handlers(app)


# Routes
app.include_router(regions_router, prefix="/api")