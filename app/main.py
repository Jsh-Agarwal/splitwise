import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from routes import router
from database import test_connection, engine, Base, AsyncSessionLocal
from models import Expense, SplitType
from schemas import CreateExpense, UpdateExpense, ExpenseResponse
import crud

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

# Add CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React default
        "http://localhost:8080",  # Vue default
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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
        # Test database connection
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
    
    # Test database connection on startup
    try:
        db_connected = await test_connection()
        if db_connected:
            logger.info("✅ Database connection established")
        else:
            logger.warning("⚠️ Database connection failed during startup")
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

async def create_tables():
    """Create all database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False

async def test_schemas():
    """Test Pydantic schema validation."""
    try:
        # Test valid equal split
        expense_data = {
            "amount": 100.0,
            "description": "Dinner at restaurant",
            "paid_by": "Om",
            "participants": ["Om", "Shantanu", "Sanket"],
            "split_type": "equal"
        }
        expense = CreateExpense(**expense_data)
        print(f"✅ Equal split schema test passed: {expense.description}")
        
        # Test valid percentage split
        percentage_data = {
            "amount": 100.0,
            "description": "Grocery shopping",
            "paid_by": "Shantanu",
            "participants": ["Om", "Shantanu", "Sanket"],
            "split_type": "percentage",
            "shares": {"Om": 40.0, "Shantanu": 35.0, "Sanket": 25.0}
        }
        percentage_expense = CreateExpense(**percentage_data)
        print(f"✅ Percentage split schema test passed: {percentage_expense.description}")
        
        # Test valid exact split
        exact_data = {
            "amount": 150.0,
            "description": "Movie tickets",
            "paid_by": "Sanket",
            "participants": ["Om", "Shantanu", "Sanket"],
            "split_type": "exact",
            "shares": {"Om": 50.0, "Shantanu": 50.0, "Sanket": 50.0}
        }
        exact_expense = CreateExpense(**exact_data)
        print(f"✅ Exact split schema test passed: {exact_expense.description}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Schema validation test failed: {e}")
        return False

async def run_crud_tests():
    """Test all CRUD operations."""
    try:
        async with AsyncSessionLocal() as db:
            print("\n🧪 Testing CRUD Operations...")
            
            # Test 1: Create equal split expense
            print("\n1. Testing equal split expense creation...")
            expense_data = CreateExpense(
                amount=120.0,
                description="Team lunch",
                paid_by="Jsh",
                participants=["Jsh", "Om", "Sanket"],
                split_type="equal"
            )
            expense1 = await crud.create_expense(expense_data, db)
            expense1_id = expense1.id  # Capture ID immediately
            print(f"✅ Equal split expense created: ID={expense1_id}, Amount={expense1.amount}")
            
            # Test 2: Create percentage split expense
            print("\n2. Testing percentage split expense creation...")
            percentage_data = CreateExpense(
                amount=100.0,
                description="Grocery shopping",
                paid_by="Om",
                participants=["Jsh", "Om", "Sanket"],
                split_type="percentage",
                shares={"Jsh": 30.0, "Om": 45.0, "Sanket": 25.0}
            )
            expense2 = await crud.create_expense(percentage_data, db)
            expense2_id = expense2.id  # Capture ID immediately
            print(f"✅ Percentage split expense created: ID={expense2_id}")
            
            # Test 3: Create exact split expense
            print("\n3. Testing exact split expense creation...")
            exact_data = CreateExpense(
                amount=90.0,
                description="Movie tickets",
                paid_by="Sanket",
                participants=["Jsh", "Om", "Sanket"],
                split_type="exact",
                shares={"Jsh": 30.0, "Om": 30.0, "Sanket": 30.0}
            )
            expense3 = await crud.create_expense(exact_data, db)
            expense3_id = expense3.id  # Capture ID immediately
            print(f"✅ Exact split expense created: ID={expense3_id}")
            
            # Test 4: Get all expenses
            print("\n4. Testing get all expenses...")
            all_expenses = await crud.get_all_expenses(db)
            print(f"✅ Retrieved {len(all_expenses)} expenses")
            for exp in all_expenses:
                print(f"   - ID: {exp.id}, Description: {exp.description}, Amount: {exp.amount}")
            
            # Test 5: Get expense by ID
            print("\n5. Testing get expense by ID...")
            retrieved_expense = await crud.get_expense_by_id(expense1_id, db)
            if retrieved_expense:
                print(f"✅ Retrieved expense: {retrieved_expense.description}")
            else:
                print("❌ Expense not found")
            
            # Test 6: Update expense
            print("\n6. Testing expense update...")
            update_data = UpdateExpense(
                amount=150.0,
                description="Updated team lunch",
                category="Food"
            )
            updated_expense = await crud.update_expense(expense1_id, update_data, db)
            if updated_expense:
                print(f"✅ Expense updated: Amount={updated_expense.amount}, Description={updated_expense.description}")
            else:
                print("❌ Update failed")
            
            # Test 7: Test validation errors
            print("\n7. Testing validation errors...")
            try:
                invalid_data = CreateExpense(
                    amount=100.0,
                    description="Invalid expense",
                    paid_by="NonParticipant",
                    participants=["Jsh", "Om"],
                    split_type="equal"
                )
                await crud.create_expense(invalid_data, db)
                print("❌ Validation should have failed")
            except ValueError as e:
                print(f"✅ Validation error caught: {e}")
            
            # Test 8: Delete expense (using captured ID)
            print("\n8. Testing expense deletion...")
            deleted = await crud.delete_expense(expense3_id, db)
            if deleted:
                print(f"✅ Expense {expense3_id} deleted successfully")
                
                # Verify deletion in a new query
                try:
                    deleted_expense = await crud.get_expense_by_id(expense3_id, db)
                    if deleted_expense is None:
                        print("✅ Deletion verified - expense not found")
                    else:
                        print("❌ Expense still exists after deletion")
                except Exception as e:
                    print(f"Error verifying deletion: {e}")
            else:
                print("❌ Delete failed")
            
            print("\n🎉 All CRUD tests completed!")
            return True
            
    except Exception as e:
        logger.error(f"❌ CRUD tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_financial_endpoints():
    """Test the financial calculation endpoints."""
    try:
        async with AsyncSessionLocal() as db:
            print("\n💰 Testing Financial Endpoints...")
            
            # Test balances calculation
            print("\n1. Testing balance calculations...")
            balances = await crud.calculate_balances(db)
            print(f"✅ Calculated balances for {len(balances)} people:")
            for balance in balances:
                print(f"   - {balance['person']}: Spent ${balance['spent']:.2f}, Owes ${balance['owed']:.2f}, Balance ${balance['balance']:.2f}")
            
            # Test settlements calculation
            print("\n2. Testing settlement calculations...")
            settlements = await crud.calculate_settlements(db)
            print(f"✅ Generated {len(settlements)} settlement transactions:")
            for settlement in settlements:
                print(f"   - {settlement['from']} pays {settlement['to']}: ${settlement['amount']:.2f}")
            
            if not settlements:
                print("   - All balances are settled!")
            
            # Test people listing
            print("\n3. Testing people listing...")
            people = await crud.get_all_people(db)
            print(f"✅ Found {len(people)} unique people: {', '.join(people)}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Financial endpoint tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🔄 Testing database connection...")
    db_success = await test_connection()
    
    if db_success:
        print("\n🔄 Creating database tables...")
        table_success = await create_tables()
        
        if table_success:
            print("\n🔄 Testing Pydantic schemas...")
            schema_success = await test_schemas()
            
            if schema_success:
                print("\n🔄 Running CRUD tests...")
                crud_success = await run_crud_tests()
                
                if crud_success:
                    print("\n🔄 Testing financial endpoints...")
                    financial_success = await test_financial_endpoints()
                    
                    if financial_success:
                        print("\n🎉 All tests passed! Database, models, CRUD, and financial operations are ready.")
                        print("\n📝 Next steps:")
                        print("   - Run FastAPI server: uvicorn routes:router --reload")
                        print("   - Test endpoints at: http://localhost:8000/docs")
                    else:
                        print("\n❌ Financial endpoint tests failed!")
                else:
                    print("\n❌ CRUD tests failed!")
            else:
                print("\n❌ Schema tests failed!")
        else:
            print("\n❌ Table creation failed!")
    else:
        print("\n❌ Database connection failed!")

# Main entry point for development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
