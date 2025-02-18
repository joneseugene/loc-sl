import redis
from fastapi_limiter import FastAPILimiter


def init_rate_limiter():
    try:
        my_redis = redis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)

        # Test Redis connection
        my_redis.ping()  
        FastAPILimiter.init(my_redis) 
        print("Rate limiter initialized successfully.")
    except Exception as e:
        print(f"Error initializing Redis: {e}")