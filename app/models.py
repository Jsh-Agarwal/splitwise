from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, Enum as SQLEnum, CheckConstraint
from sqlalchemy.sql import func
from database import Base
import enum

class SplitType(enum.Enum):
    equal = "equal"
    percentage = "percentage"
    exact = "exact"

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    paid_by = Column(String, nullable=False)
    participants = Column(JSON, nullable=False)  # List of participant names
    split_type = Column(SQLEnum(SplitType), nullable=False, default=SplitType.equal)
    shares = Column(JSON, nullable=True)  # Dict of {participant: amount/percentage}
    category = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Add constraint to ensure amount is positive
    __table_args__ = (
        CheckConstraint('amount > 0', name='positive_amount'),
    )
    
    def __repr__(self):
        return f"<Expense(id={self.id}, description='{self.description}', amount={self.amount}, paid_by='{self.paid_by}')>"
