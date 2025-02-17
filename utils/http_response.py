# core/utils.py
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, List, Union

def success_response(data: Union[BaseModel, List[BaseModel], dict, List[dict], None] = None, status_code: int = 200, message: str = "success"):
    if isinstance(data, list):
        # Ensure all items are dictionaries
        data = [item.dict() if isinstance(item, BaseModel) else item for item in data]
    elif isinstance(data, BaseModel):
        data = data.dict()
    elif isinstance(data, dict):
        pass  # Already a dictionary, do nothing
    else:
        data = []

    return JSONResponse(
        status_code=200,
        content={
            "status": "1",
            "status_code": status_code,
            "message": message,
            "error": "",
            "data": data
        }
    )


def error_response(status_code: int, error_message: str):
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "0",
            "status_code": status_code,
            "error_message": error_message,
            "message": "error",
            "data": []
        }
    )
    
