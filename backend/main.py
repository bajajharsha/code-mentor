import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config.settings import get_settings
from app.config.database import connect_to_mongodb, close_mongodb_connection
from app.apis import auth_route, resync_route, query_route, llm_rewrite

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    await connect_to_mongodb()
    yield
    # Shutdown: Close MongoDB connection
    await close_mongodb_connection()

# Include routers
app.include_router(auth_route.router, prefix=settings.API_PREFIX)
app.include_router(resync_route.router, prefix=settings.API_PREFIX)
app.include_router(query_route.router, prefix=settings.API_PREFIX)
app.include_router(llm_rewrite.router, prefix=settings.API_PREFIX)

@app.get("/")
async def root():
    return {"message": "Auth API is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)