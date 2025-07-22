import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os

from app.routes import router
from app.database import test_connection, engine, Base, AsyncSessionLocal
from app.models import Expense, SplitType
from app.schemas import CreateExpense, UpdateExpense, ExpenseResponse
import app.crud as crud

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="Splitwise API",
    description="A expense sharing and bill splitting API built with FastAPI and PostgreSQL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for frontend development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React default
        "http://localhost:8080",  # Vue default
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173",
        # Production frontend domains
        "https://*.vercel.app",
        "https://*.netlify.app",
        "https://*.onrender.com",
    ],
    allow_origin_regex=r"https://.*\\.vercel\\.app|https://.*\\.netlify\\.app|https://.*\\.onrender\\.com|http://localhost:\\d+|http://127.0.0.1:\\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes from routes.py
app.include_router(router, prefix="/api/v1", tags=["expenses"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Splitwise API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_healthy = await test_connection()
        if db_healthy:
            return {
                "status": "healthy",
                "database": "connected",
                "message": "All systems operational"
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "database": "disconnected",
                    "message": "Database connection failed"
                }
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "error",
                "message": f"Health check error: {str(e)}"
            }
        )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🚀 Splitwise API is starting up...")
    try:
        db_connected = await test_connection()
        if db_connected:
            logger.info("✅ Database connection established")
        else:
            logger.warning("⚠️ Database connection failed during startup")
        # Create tables on startup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created or already exist.")
    except Exception as e:
        logger.error(f"❌ Database connection error during startup: {e}")
    logger.info("🎉 Splitwise API startup complete!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("🛑 Splitwise API is shutting down...")
    logger.info("👋 Goodbye!")

# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The endpoint {request.url.path} was not found",
            "docs": "/docs"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "docs": "/docs"
        }
    )

# Main entry point for local development only
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
