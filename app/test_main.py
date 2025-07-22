from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.routes import router as expense_router
from app.database import engine, Base, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# Create the FastAPI app instance
app = FastAPI(
    title="Splitwise Clone API",
    description="API for managing expenses and settlements",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
origins = [
    "http://localhost:3000",  # Frontend app
    "https://your-production-domain.com",  # Production domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the expense router
app.include_router(expense_router, prefix="/api")

@app.on_event("startup")
async def startup():
    """Startup event to create database tables."""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created or already exist.")
        
@app.on_event("shutdown")
async def shutdown():
    """Shutdown event to clean up resources."""
    # Here you can add any cleanup code if needed
    print("🔒 Shutting down...")

@app.get("/", response_model=str)
async def read_root():
    """Root endpoint."""
    return "Welcome to the Splitwise Clone API!"

# Dependency to get database session in production
async def get_db_production() -> AsyncSession:
    """Get database session for production use."""
    async with get_db() as session:
        yield session

# Run the application with: uvicorn main:app --reload
if __name__ == "__main__":
    import os
    # Set environment variable for database URL if not already set
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:password@localhost/dbname"
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")