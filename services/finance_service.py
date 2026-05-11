from database.session import Session
from database.models import Expense, Goal, GoalHistory
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

def add_expense(amount: float, category: str, description: str = ""):
    with Session() as session:
        new_exp = Expense(amount=amount, category=category, description=description)
        session.add(new_exp)
        session.commit()

def get_all_expenses():
    with Session() as session:
        return session.query(Expense).order_by(Expense.created_at.desc()).all()

def get_expense_report():
    with Session() as session:
        expenses = session.query(Expense).all()
        if not expenses: return "Витрат немає."
        total = sum(e.amount for e in expenses)
        return f"Загалом: {total:.0f} грн"

def create_goal(name: str, target: float):
    with Session() as session:
        new_goal = Goal(name=name, target_amount=target)
        session.add(new_goal)
        session.commit()
        return f"Ціль '{name}' створена!"

def get_all_goals():
    with Session() as session:
        return session.query(Goal).all()

def add_to_goal(goal_name: str, amount: float, description: str = ""):
    with Session() as session:
        goal = session.query(Goal).filter_by(name=goal_name).first()
        if goal:
            goal.current_amount += amount
            history = GoalHistory(goal_id=goal.id, amount=amount, description=description)
            session.add(history)
            session.commit()
            return f"Додано {amount} до {goal_name}"
        return "Ціль не знайдена."
def delete_history_record(record_id: int):
    with Session() as session:
        record = session.query(GoalHistory).get(record_id)
        if record:
            goal = record.goal
            goal.current_amount -= record.amount
            session.delete(record)
            session.commit()
            return True
        return False
