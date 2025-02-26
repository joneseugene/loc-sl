from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

rate_limit_store = {}

async def rate_limit_middleware(request: Request, call_next):
    ip = request.client.host  # Client IP
    route = request.url.path  # Requested route

    now = datetime.utcnow()

    # Initialize IP and route tracking
    if ip not in rate_limit_store:
        rate_limit_store[ip] = {}
    
    if route not in rate_limit_store[ip]:
        rate_limit_store[ip][route] = []

    # Remove expired timestamps (older than 1 minute)
    rate_limit_store[ip][route] = [t for t in rate_limit_store[ip][route] if now - t < timedelta(minutes=1)]

    # Enforce limit: 5 requests per minute per route
    if len(rate_limit_store[ip][route]) >= 5:
        response_data = {
            "status": "failure",
            "status_code": 429,
            "error_message": "Too many requests for this endpoint. Try again later.",
            "data": []
        }
        return JSONResponse(content=response_data, status_code=429)

    rate_limit_store[ip][route].append(now)

    response = await call_next(request)
    return response
