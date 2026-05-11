from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.base import Base
# Обов'язково імпортуй моделі, щоб Base про них знав
from database.models import Expense, Goal, GoalHistory 

engine = create_engine('sqlite:///spendly.db')
# Цей рядок автоматично створить таблиці, якщо їх немає:
Base.metadata.create_all(bind=engine) 

Session = sessionmaker(bind=engine)
