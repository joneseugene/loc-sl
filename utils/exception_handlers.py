from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from .http_response import error_response 
import traceback

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        print("Unhandled Exception:", traceback.format_exc())
        return error_response(status_code=exc.status_code, error_message=exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return error_response(status_code=422, error_message="Validation Error")

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        return error_response(status_code=400, error_message="Database Integrity Error")

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return error_response(status_code=500, error_message="Internal Server Error")
