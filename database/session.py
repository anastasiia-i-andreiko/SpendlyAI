from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.base import Base

# Створюємо двигун бази даних
engine = create_engine("sqlite:///./spendly.db", connect_args={"check_same_thread": False})
# Створюємо фабрику сесій
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
