from sqlalchemy import Column, Integer, String, Float, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.base import Base

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)  # Хто зробив запит
    amount = Column(Float)
    category = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.now)

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)  # Власник цілі
    name = Column(String)
    target_amount = Column(Float)
    current_amount = Column(Float, default=0.0)
    history = relationship("GoalHistory", back_populates="goal", cascade="all, delete-orphan")

class GoalHistory(Base):
    __tablename__ = "goal_history"
    id = Column(Integer, primary_key=True)
    goal_id = Column(Integer, ForeignKey("goals.id"))
    amount = Column(Float)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    goal = relationship("Goal", back_populates="history")