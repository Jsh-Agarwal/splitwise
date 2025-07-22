from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db, test_connection
from app.schemas import (
    CreateExpense, UpdateExpense, ExpenseResponse,
    BalanceSummary, SettlementTransaction, PeopleList, ApiResponse
)
import app.crud as crud

router = APIRouter()

# Health check endpoint
@router.get("/health", response_model=ApiResponse)
async def health_check():
    """Check database connection health"""
    try:
        is_connected = await test_connection()
        if is_connected:
            return ApiResponse(
                success=True,
                message="Database connection successful",
                data={"status": "healthy"}
            )
        else:
            return ApiResponse(
                success=False,
                message="Database connection failed",
                data={"status": "unhealthy"}
            )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Health check error: {str(e)}",
            data={"status": "error"}
        )

# Expense endpoints
def serialize_expense(expense) -> dict:
    """Convert SQLAlchemy Expense object to serializable dictionary"""
    return {
        "id": expense.id,
        "amount": expense.amount,
        "description": expense.description,
        "paid_by": expense.paid_by,
        "participants": expense.participants,
        "split_type": expense.split_type.value,
        "shares": expense.shares,
        "category": expense.category,
        "created_at": expense.created_at.isoformat() if expense.created_at else None
    }

@router.post("/expenses", response_model=ApiResponse)
async def create_expense(expense: CreateExpense, db: AsyncSession = Depends(get_db)):
    """Create a new expense"""
    try:
        created_expense = await crud.create_expense(expense, db)
        return ApiResponse(
            success=True,
            message="Expense created successfully",
            data=serialize_expense(created_expense)
        )
    except ValueError as e:
        return ApiResponse(
            success=False,
            message=f"Validation error: {str(e)}",
            data=None
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Internal server error",
            data=None
        )

@router.get("/expenses", response_model=ApiResponse)
async def get_expenses(db: AsyncSession = Depends(get_db)):
    """Get all expenses"""
    try:
        expenses = await crud.get_all_expenses(db)
        expense_data = [serialize_expense(expense) for expense in expenses]
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(expenses)} expenses",
            data=expense_data
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Internal server error",
            data=None
        )

@router.get("/expenses/{expense_id}", response_model=ApiResponse)
async def get_expense(expense_id: int, db: AsyncSession = Depends(get_db)):
    """Get expense by ID"""
    try:
        expense = await crud.get_expense_by_id(expense_id, db)
        if not expense:
            return ApiResponse(
                success=False,
                message="Expense not found",
                data=None
            )
        
        return ApiResponse(
            success=True,
            message="Expense retrieved successfully",
            data=serialize_expense(expense)
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Internal server error",
            data=None
        )

@router.put("/expenses/{expense_id}", response_model=ApiResponse)
async def update_expense(expense_id: int, expense_data: UpdateExpense, db: AsyncSession = Depends(get_db)):
    """Update an expense"""
    try:
        expense = await crud.update_expense(expense_id, expense_data, db)
        if not expense:
            return ApiResponse(
                success=False,
                message="Expense not found",
                data=None
            )
        
        return ApiResponse(
            success=True,
            message="Expense updated successfully",
            data=serialize_expense(expense)
        )
    except ValueError as e:
        return ApiResponse(
            success=False,
            message=f"Validation error: {str(e)}",
            data=None
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Internal server error",
            data=None
        )

@router.delete("/expenses/{expense_id}", response_model=ApiResponse)
async def delete_expense(expense_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an expense"""
    try:
        deleted = await crud.delete_expense(expense_id, db)
        if not deleted:
            return ApiResponse(
                success=False,
                message="Expense not found",
                data=None
            )
        
        return ApiResponse(
            success=True,
            message="Expense deleted successfully",
            data={"deleted_id": expense_id}
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Internal server error",
            data=None
        )

# Financial endpoints
@router.get("/balances", response_model=ApiResponse)
async def get_balances(db: AsyncSession = Depends(get_db)):
    """Get balance summary for all people"""
    try:
        balances = await crud.calculate_balances(db)
        if not balances:
            return ApiResponse(
                success=True,
                message="No expenses found",
                data=[]
            )
        
        return ApiResponse(
            success=True,
            message=f"Retrieved balances for {len(balances)} people",
            data=balances
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Internal server error",
            data=None
        )

@router.get("/settlements", response_model=ApiResponse)
async def get_settlements(db: AsyncSession = Depends(get_db)):
    """Get simplified settlement transactions"""
    try:
        settlements = await crud.calculate_settlements(db)
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(settlements)} settlements",
            data=settlements
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Internal server error",
            data=None
        )

@router.get("/people", response_model=ApiResponse)
async def get_people(db: AsyncSession = Depends(get_db)):
    """Get all people who have participated in expenses"""
    try:
        people = await crud.get_all_people(db)
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(people)} people",
            data={"people": people}
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Internal server error",
            data=None
        )
