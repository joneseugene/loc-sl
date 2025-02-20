from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from utils.http_response import error_response 
import traceback


def register_exception_handlers(app: FastAPI):
    # Catch HTTP exceptions
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        print("Unhandled Exception:", traceback.format_exc())
        return error_response(status_code=exc.status_code, error_message=exc.detail)

    # Catch validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        content_type = request.headers.get("Content-Type")
        # Check if the request type is text/csv
        if content_type == "text/csv":
            return error_response(status_code=400, error_message="Invalid CSV content format")
        return error_response(status_code=422, error_message="Validation Error")

    # Catch integrity errors (like DB constraints)
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        return error_response(status_code=400, error_message="Database Integrity Error")

    # Catch all general errors
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        content_type = request.headers.get("Content-Type")
        # Check if content type is CSV, and handle accordingly
        if content_type == "text/csv":
            return error_response(status_code=500, error_message="Internal CSV processing error")
        return error_response(status_code=500, error_message="Internal Server Error")
