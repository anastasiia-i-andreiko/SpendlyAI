from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.base import Base
# Обов'язково імпортуємо моделі тут
from database.models import Expense, Goal, GoalHistory

engine = create_engine('sqlite:///spendly.db')

# Цей рядок автоматично створює таблиці, якщо їх немає в файлі .db
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
