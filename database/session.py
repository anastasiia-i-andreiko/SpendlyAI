from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.base import Base
# Імпортуємо моделі, щоб Base знав, які таблиці створювати
from database.models import Expense, Goal, GoalHistory 

engine = create_engine('sqlite:///spendly.db')

# Ця команда створює таблиці в базі даних автоматично
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
