from pydantic import BaseModel, validator, Field
from typing import List, Optional, Dict, Literal, Any, Union
from datetime import datetime

class BaseExpense(BaseModel):
    amount: float = Field(..., gt=0, description="Amount must be positive")
    description: str = Field(..., min_length=1, description="Description cannot be empty")
    paid_by: str = Field(..., min_length=1, description="Payer name cannot be empty")
    participants: List[str] = Field(..., min_items=1, description="At least one participant required")
    split_type: Literal["equal", "percentage", "exact"] = "equal"
    shares: Optional[Dict[str, float]] = None
    category: Optional[str] = None
    
    @validator('participants')
    def participants_not_empty(cls, v):
        if not v or any(not participant.strip() for participant in v):
            raise ValueError('All participants must have non-empty names')
        # Remove duplicates while preserving order
        seen = set()
        unique_participants = []
        for participant in v:
            if participant not in seen:
                seen.add(participant)
                unique_participants.append(participant)
        return unique_participants
    
    @validator('paid_by')
    def paid_by_in_participants(cls, v, values):
        if 'participants' in values and v not in values['participants']:
            raise ValueError('paid_by must be one of the participants')
        return v
    
    @validator('shares')
    def validate_shares(cls, v, values):
        if 'split_type' not in values or 'participants' not in values:
            return v
            
        split_type = values['split_type']
        participants = values['participants']
        
        if split_type == 'equal':
            if v is not None:
                raise ValueError('shares should not be provided for equal split')
            return v
        
        if split_type in ['percentage', 'exact']:
            if v is None:
                raise ValueError(f'shares must be provided for {split_type} split')
            
            # Check if all participants have shares
            missing_participants = set(participants) - set(v.keys())
            if missing_participants:
                raise ValueError(f'Missing shares for participants: {missing_participants}')
            
            # Check if there are extra participants in shares
            extra_participants = set(v.keys()) - set(participants)
            if extra_participants:
                raise ValueError(f'Shares provided for non-participants: {extra_participants}')
            
            # For percentage split, check if percentages sum to 100
            if split_type == 'percentage':
                total_percentage = sum(v.values())
                if abs(total_percentage - 100) > 0.01:  # Allow small floating point errors
                    raise ValueError(f'Percentages must sum to 100, got {total_percentage}')
            
            # For exact split, check if amounts sum to total amount
            if split_type == 'exact' and 'amount' in values:
                total_shares = sum(v.values())
                if abs(total_shares - values['amount']) > 0.01:  # Allow small floating point errors
                    raise ValueError(f'Exact shares must sum to total amount {values["amount"]}, got {total_shares}')
        
        return v

class CreateExpense(BaseExpense):
    pass

class UpdateExpense(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=1)
    paid_by: Optional[str] = Field(None, min_length=1)
    participants: Optional[List[str]] = Field(None, min_items=1)
    split_type: Optional[Literal["equal", "percentage", "exact"]] = None
    shares: Optional[Dict[str, float]] = None
    category: Optional[str] = None
    
    # Apply same validators as BaseExpense for non-None values
    @validator('participants')
    def participants_not_empty(cls, v):
        if v is not None:
            return BaseExpense.participants_not_empty(v)
        return v

class ExpenseResponse(BaseExpense):
    id: int
    created_at: datetime
    
    @validator('split_type', pre=True)
    def convert_enum_to_string(cls, v):
        """Convert SQLAlchemy enum to string for serialization"""
        if hasattr(v, 'value'):
            return v.value
        return v
    
    class Config:
        from_attributes = True  # SQLAlchemy 2.x style (replaces orm_mode)

class BalanceSummary(BaseModel):
    person: str
    spent: float
    owed: float
    balance: float

class SettlementTransaction(BaseModel):
    from_: str = Field(..., alias="from")
    to: str
    amount: float
    
    class Config:
        populate_by_name = True  # Pydantic v2 style (replaces allow_population_by_field_name)

class PeopleList(BaseModel):
    people: List[str]

# API Response wrapper models
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Union[Dict[str, Any], List[Any], str, int, float]] = None
