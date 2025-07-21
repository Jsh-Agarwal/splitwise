from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from schemas import (
    CreateExpense, UpdateExpense, ExpenseResponse,
    BalanceSummary, SettlementTransaction, PeopleList, ApiResponse
)
import crud

router = APIRouter()

# Expense endpoints
@router.post("/expenses", response_model=ExpenseResponse)
async def create_expense(expense: CreateExpense, db: AsyncSession = Depends(get_db)):
    """Create a new expense"""
    try:
        return await crud.create_expense(expense, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/expenses", response_model=List[ExpenseResponse])
async def get_expenses(db: AsyncSession = Depends(get_db)):
    """Get all expenses"""
    try:
        expenses = await crud.get_all_expenses(db)
        return expenses
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
async def get_expense(expense_id: int, db: AsyncSession = Depends(get_db)):
    """Get expense by ID"""
    try:
        expense = await crud.get_expense_by_id(expense_id, db)
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        return expense
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(expense_id: int, expense_data: UpdateExpense, db: AsyncSession = Depends(get_db)):
    """Update an expense"""
    try:
        expense = await crud.update_expense(expense_id, expense_data, db)
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        return expense
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an expense"""
    try:
        deleted = await crud.delete_expense(expense_id, db)
        if not deleted:
            raise HTTPException(status_code=404, detail="Expense not found")
        return {"success": True, "message": "Expense deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# Financial endpoints
@router.get("/balances", response_model=List[BalanceSummary])
async def get_balances(db: AsyncSession = Depends(get_db)):
    """Get balance summary for all people"""
    try:
        balances = await crud.calculate_balances(db)
        if not balances:
            raise HTTPException(status_code=404, detail="No expenses found.")
        return balances
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/settlements", response_model=List[SettlementTransaction])
async def get_settlements(db: AsyncSession = Depends(get_db)):
    """Get simplified settlement transactions"""
    try:
        settlements = await crud.calculate_settlements(db)
        if not settlements:
            return []  # Return empty list with message in a wrapper if needed
        return settlements
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/people", response_model=PeopleList)
async def get_people(db: AsyncSession = Depends(get_db)):
    """Get all people who have participated in expenses"""
    try:
        people = await crud.get_all_people(db)
        return PeopleList(people=people)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
