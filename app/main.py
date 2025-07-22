import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

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
    description="""
A production-ready expense sharing and bill splitting API built with FastAPI and PostgreSQL.

**How to Use:**
- All endpoints are under `/api/v1`.
- To create or update an expense, you must provide a valid JSON body matching the required schema.
- See the `/docs` tab for interactive API usage and example requests.

**Expense Requirements:**
- `amount` (float): Must be positive.
- `description` (string): Required, cannot be empty.
- `paid_by` (string): Must be one of the `participants`.
- `participants` (list of strings): At least one, all must be non-empty.
- `split_type` (string): One of `equal`, `percentage`, or `exact`.
- `shares` (dict):
    - For `equal` split: Omit this field.
    - For `percentage` split: Required, must sum to 100, keys must match participants.
    - For `exact` split: Required, must sum to `amount`, keys must match participants.
- `category` (string, optional): Any string.

**Sample Requests:**

*POST /api/v1/expenses* (Equal split)
```json
{
  "amount": 120.0,
  "description": "Team lunch",
  "paid_by": "Alice",
  "participants": ["Alice", "Bob", "Charlie"],
  "split_type": "equal",
  "category": "Food"
}
```

*POST /api/v1/expenses* (Percentage split)
```json
{
  "amount": 200.0,
  "description": "Groceries",
  "paid_by": "Bob",
  "participants": ["Alice", "Bob", "Charlie"],
  "split_type": "percentage",
  "shares": {
    "Alice": 40.0,
    "Bob": 40.0,
    "Charlie": 20.0
  },
  "category": "Groceries"
}
```

*POST /api/v1/expenses* (Exact split)
```json
{
  "amount": 150.0,
  "description": "Movie tickets",
  "paid_by": "Charlie",
  "participants": ["Alice", "Bob", "Charlie"],
  "split_type": "exact",
  "shares": {
    "Alice": 50.0,
    "Bob": 50.0,
    "Charlie": 50.0
  },
  "category": "Entertainment"
}
```

*PUT /api/v1/expenses/{expense_id}* (Update amount and description)
```json
{
  "amount": 180.0,
  "description": "Updated team lunch"
}
```

*PUT /api/v1/expenses/{expense_id}* (Update split type and shares)
```json
{
  "split_type": "percentage",
  "shares": {
    "Alice": 50.0,
    "Bob": 30.0,
    "Charlie": 20.0
  }
}
```

*PUT /api/v1/expenses/{expense_id}* (Update category only)
```json
{
  "category": "Dining"
}
```

*DELETE /api/v1/expenses/{expense_id}*
- No request body required. Just call the endpoint with the correct `expense_id` in the URL.

**Common Error Cases:**
- 422 Unprocessable Entity: Your request body is missing required fields, has wrong types, or fails validation (see error details in response).
- 400 Bad Request: Business logic error (e.g., `paid_by` not in `participants`, shares do not sum correctly).
- 404 Not Found: Resource does not exist.
- 500 Internal Server Error: Unexpected server error.

**If you get a 422 error:**
- Check the error response for the exact field and reason.
- Make sure your JSON matches the schema and all requirements above.
- Example error:
    ```json
    {
      "detail": [
        {
          "loc": ["body", "amount"],
          "msg": "field required",
          "type": "value_error.missing"
        }
      ]
    }
    ```
- For more help, see the schema in `/docs` or `/openapi.json`.
""",
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

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom handler for 422 Unprocessable Entity errors with detailed feedback."""
    logger.warning(f"Validation error at {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Your request did not match the required schema. See 'details' for more information.",
            "details": exc.errors(),
            "body": exc.body,
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
