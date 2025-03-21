from fastapi.responses import JSONResponse
from functools import wraps
from fastapi import status

def handle_exceptions(func):
    """A decorator to catch exceptions and return a consistent JSON error response."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "data": {},
                    "statuscode": 500,
                    "detail": "An internal server error occurred.",
                    "error": str(e),
                },
            )
    return wrapper
