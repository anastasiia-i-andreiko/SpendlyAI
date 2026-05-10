from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.base import Base


class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    amount = Column(Float)
    category = Column(String)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class SavingsGoal(Base):
    __tablename__ = "savings_goals"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    target_amount = Column(Float)
    current_amount = Column(Float, default=0.0)
    history = relationship("SavingsHistory", back_populates="goal", cascade="all, delete-orphan")


class SavingsHistory(Base):
    __tablename__ = "savings_history"
    id = Column(Integer, primary_key=True)
    goal_id = Column(Integer, ForeignKey("savings_goals.id"))
    amount = Column(Float)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    goal = relationship("SavingsGoal", back_populates="history")
