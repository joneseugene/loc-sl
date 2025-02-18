from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter

async def rate_limiter_middleware(request: Request, call_next):
    redis = FastAPILimiter.redis
    if redis is None:
        return JSONResponse(status_code=500, content={"detail": "Rate limiter not initialized"})

    identifier = request.client.host  # Use client IP as key
    limit_key = f"api:rate-limit:{identifier}"

    current = await redis.get(limit_key)

    if current and int(current) >= 5:  # Limit: 5 requests per minute
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})

    await redis.incr(limit_key)
    await redis.expire(limit_key, 60)  # Expire key after 60 seconds

    return await call_next(request)
