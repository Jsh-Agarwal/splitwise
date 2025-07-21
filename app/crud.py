from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict
import logging

from models import Expense, SplitType
from schemas import CreateExpense, UpdateExpense

logger = logging.getLogger(__name__)

async def create_expense(expense_data: CreateExpense, db: AsyncSession) -> Expense:
    """
    Create a new expense with validation for split logic.
    """
    try:
        # Validate amount
        if expense_data.amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Validate paid_by is in participants
        if expense_data.paid_by not in expense_data.participants:
            raise ValueError("paid_by must be one of the participants")
        
        # Validate split logic
        _validate_split_logic(expense_data)
        
        # Create expense instance
        db_expense = Expense(
            amount=expense_data.amount,
            description=expense_data.description,
            paid_by=expense_data.paid_by,
            participants=expense_data.participants,
            split_type=SplitType(expense_data.split_type),
            shares=expense_data.shares,
            category=expense_data.category
        )
        
        db.add(db_expense)
        await db.commit()
        await db.refresh(db_expense)
        
        logger.info(f"Created expense: {db_expense.id} - {db_expense.description}")
        return db_expense
        
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error creating expense: {e}")
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating expense: {e}")
        raise

async def get_all_expenses(db: AsyncSession) -> List[Expense]:
    """
    Get all expenses ordered by created_at DESC.
    """
    try:
        result = await db.execute(
            select(Expense).order_by(Expense.created_at.desc())
        )
        expenses = result.scalars().all()
        logger.info(f"Retrieved {len(expenses)} expenses")
        return list(expenses)
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving expenses: {e}")
        raise

async def get_expense_by_id(expense_id: int, db: AsyncSession) -> Optional[Expense]:
    """
    Get a single expense by ID.
    """
    try:
        result = await db.execute(
            select(Expense).where(Expense.id == expense_id)
        )
        expense = result.scalar_one_or_none()
        
        if expense:
            logger.info(f"Retrieved expense: {expense_id}")
        else:
            logger.info(f"Expense not found: {expense_id}")
        
        return expense
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving expense {expense_id}: {e}")
        raise

async def update_expense(expense_id: int, expense_data: UpdateExpense, db: AsyncSession) -> Optional[Expense]:
    """
    Update an expense with validation.
    """
    try:
        # First, get the existing expense
        existing_expense = await get_expense_by_id(expense_id, db)
        if not existing_expense:
            return None
        
        # Prepare update data, keeping existing values for None fields
        update_data = {}
        
        if expense_data.amount is not None:
            if expense_data.amount <= 0:
                raise ValueError("Amount must be positive")
            update_data['amount'] = expense_data.amount
        
        if expense_data.description is not None:
            update_data['description'] = expense_data.description
        
        if expense_data.paid_by is not None:
            update_data['paid_by'] = expense_data.paid_by
        
        if expense_data.participants is not None:
            update_data['participants'] = expense_data.participants
        
        if expense_data.split_type is not None:
            update_data['split_type'] = SplitType(expense_data.split_type)
        
        if expense_data.shares is not None:
            update_data['shares'] = expense_data.shares
        
        if expense_data.category is not None:
            update_data['category'] = expense_data.category
        
        # Create a temporary object for validation
        temp_data = {
            'amount': update_data.get('amount', existing_expense.amount),
            'description': update_data.get('description', existing_expense.description),
            'paid_by': update_data.get('paid_by', existing_expense.paid_by),
            'participants': update_data.get('participants', existing_expense.participants),
            'split_type': update_data.get('split_type', existing_expense.split_type).value if isinstance(update_data.get('split_type', existing_expense.split_type), SplitType) else update_data.get('split_type', existing_expense.split_type.value),
            'shares': update_data.get('shares', existing_expense.shares),
            'category': update_data.get('category', existing_expense.category)
        }
        
        # Validate the complete updated expense
        temp_expense = CreateExpense(**temp_data)
        _validate_split_logic(temp_expense)
        
        # Validate paid_by is in participants
        if temp_data['paid_by'] not in temp_data['participants']:
            raise ValueError("paid_by must be one of the participants")
        
        # Perform the update
        await db.execute(
            update(Expense)
            .where(Expense.id == expense_id)
            .values(**update_data)
        )
        
        await db.commit()
        
        # Return the updated expense
        updated_expense = await get_expense_by_id(expense_id, db)
        logger.info(f"Updated expense: {expense_id}")
        return updated_expense
        
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error updating expense {expense_id}: {e}")
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating expense {expense_id}: {e}")
        raise

async def delete_expense(expense_id: int, db: AsyncSession) -> bool:
    """
    Delete an expense by ID.
    """
    try:
        # Check if expense exists
        existing_expense = await get_expense_by_id(expense_id, db)
        if not existing_expense:
            return False
        
        # Delete the expense
        await db.execute(
            delete(Expense).where(Expense.id == expense_id)
        )
        
        await db.commit()
        logger.info(f"Deleted expense: {expense_id}")
        return True
        
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error deleting expense {expense_id}: {e}")
        raise

async def calculate_balances(db: AsyncSession) -> List[Dict[str, any]]:
    """
    Calculate balances for each person based on expenses.
    Returns: [{"person": str, "spent": float, "owed": float, "balance": float}]
    """
    try:
        # Get all expenses
        expenses = await get_all_expenses(db)
        
        if not expenses:
            return []
        
        # Initialize balance tracking
        balances = {}
        
        for expense in expenses:
            amount = Decimal(str(expense.amount))
            participants = expense.participants
            paid_by = expense.paid_by
            split_type = expense.split_type.value
            shares = expense.shares or {}
            
            # Initialize people if not seen before
            all_people = set([paid_by] + participants)
            for person in all_people:
                if person not in balances:
                    balances[person] = {"spent": Decimal('0'), "owed": Decimal('0')}
            
            # Add amount paid
            balances[paid_by]["spent"] += amount
            
            # Calculate what each person owes
            if split_type == "equal":
                per_person = amount / Decimal(len(participants))
                for participant in participants:
                    balances[participant]["owed"] += per_person
            
            elif split_type == "percentage":
                for participant, percentage in shares.items():
                    owed_amount = amount * (Decimal(str(percentage)) / Decimal('100'))
                    balances[participant]["owed"] += owed_amount
            
            elif split_type == "exact":
                for participant, exact_amount in shares.items():
                    balances[participant]["owed"] += Decimal(str(exact_amount))
        
        # Convert to response format with proper rounding
        result = []
        for person, data in balances.items():
            spent = float(data["spent"].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            owed = float(data["owed"].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            balance = float((data["spent"] - data["owed"]).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            
            result.append({
                "person": person,
                "spent": spent,
                "owed": owed,
                "balance": balance
            })
        
        # Sort by person name for consistency
        result.sort(key=lambda x: x["person"])
        logger.info(f"Calculated balances for {len(result)} people")
        return result
        
    except Exception as e:
        logger.error(f"Error calculating balances: {e}")
        raise

async def calculate_settlements(db: AsyncSession) -> List[Dict[str, any]]:
    """
    Calculate simplified settlements to minimize transactions.
    Returns: [{"from": str, "to": str, "amount": float}]
    """
    try:
        balances_data = await calculate_balances(db)
        
        if not balances_data:
            return []
        
        # Separate creditors (positive balance) and debtors (negative balance)
        creditors = []  # People who are owed money
        debtors = []    # People who owe money
        
        for person_data in balances_data:
            balance = Decimal(str(person_data["balance"]))
            if balance > Decimal('0.01'):  # Small threshold to handle floating point precision
                creditors.append({"person": person_data["person"], "amount": balance})
            elif balance < Decimal('-0.01'):
                debtors.append({"person": person_data["person"], "amount": abs(balance)})
        
        # Generate settlements using greedy algorithm
        settlements = []
        creditors.sort(key=lambda x: x["amount"], reverse=True)
        debtors.sort(key=lambda x: x["amount"], reverse=True)
        
        i, j = 0, 0
        while i < len(creditors) and j < len(debtors):
            creditor = creditors[i]
            debtor = debtors[j]
            
            # Calculate settlement amount
            settlement_amount = min(creditor["amount"], debtor["amount"])
            
            if settlement_amount > Decimal('0.01'):  # Only create settlement if meaningful amount
                settlements.append({
                    "from": debtor["person"],
                    "to": creditor["person"],
                    "amount": float(settlement_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
                })
            
            # Update remaining amounts
            creditor["amount"] -= settlement_amount
            debtor["amount"] -= settlement_amount
            
            # Move to next creditor/debtor if current one is settled
            if creditor["amount"] <= Decimal('0.01'):
                i += 1
            if debtor["amount"] <= Decimal('0.01'):
                j += 1
        
        logger.info(f"Calculated {len(settlements)} settlements")
        return settlements
        
    except Exception as e:
        logger.error(f"Error calculating settlements: {e}")
        raise

async def get_all_people(db: AsyncSession) -> List[str]:
    """
    Get all unique people from expenses (paid_by + participants).
    Returns: Sorted list of unique names
    """
    try:
        expenses = await get_all_expenses(db)
        
        if not expenses:
            return []
        
        people = set()
        
        for expense in expenses:
            # Add the person who paid
            people.add(expense.paid_by)
            # Add all participants
            people.update(expense.participants)
        
        # Convert to sorted list
        result = sorted(list(people))
        logger.info(f"Found {len(result)} unique people")
        return result
        
    except Exception as e:
        logger.error(f"Error getting all people: {e}")
        raise

def _validate_split_logic(expense_data: CreateExpense) -> None:
    """
    Validate split logic based on split type.
    """
    split_type = expense_data.split_type
    participants = expense_data.participants
    shares = expense_data.shares
    amount = expense_data.amount
    
    if split_type == "equal":
        if shares is not None:
            raise ValueError("shares should not be provided for equal split")
    
    elif split_type == "percentage":
        if shares is None:
            raise ValueError("shares must be provided for percentage split")
        
        # Check if all participants have shares
        missing_participants = set(participants) - set(shares.keys())
        if missing_participants:
            raise ValueError(f"Missing shares for participants: {missing_participants}")
        
        # Check if there are extra participants in shares
        extra_participants = set(shares.keys()) - set(participants)
        if extra_participants:
            raise ValueError(f"Shares provided for non-participants: {extra_participants}")
        
        # Check if percentages sum to 100
        total_percentage = sum(shares.values())
        if abs(total_percentage - 100) > 0.01:
            raise ValueError(f"Percentages must sum to 100, got {total_percentage}")
    
    elif split_type == "exact":
        if shares is None:
            raise ValueError("shares must be provided for exact split")
        
        # Check if all participants have shares
        missing_participants = set(participants) - set(shares.keys())
        if missing_participants:
            raise ValueError(f"Missing shares for participants: {missing_participants}")
        
        # Check if there are extra participants in shares
        extra_participants = set(shares.keys()) - set(participants)
        if extra_participants:
            raise ValueError(f"Shares provided for non-participants: {extra_participants}")
        
        # Check if exact amounts sum to total amount
        total_shares = sum(shares.values())
        if abs(total_shares - amount) > 0.01:
            raise ValueError(f"Exact shares must sum to total amount {amount}, got {total_shares}")
