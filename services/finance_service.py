from database.session import Session  # ОСЬ ЦЕЙ РЯДОК МАЄ БУТИ ТУТ
from database.models import Expense, Goal, GoalHistory
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from sqlalchemy import func


# --- ВИТРАТИ ---

def add_expense(user_id: int, amount: float, category: str, description: str = ""):
    with Session() as session:
        new_exp = Expense(user_id=user_id, amount=amount, category=category, description=description)
        session.add(new_exp)
        session.commit()


def get_all_expenses(user_id: int):
    with Session() as session:
        return session.query(Expense).filter_by(user_id=user_id).order_by(Expense.created_at.desc()).all()


def get_expense_report(user_id: int):
    with Session() as session:
        expenses = session.query(Expense).filter_by(user_id=user_id).all()
        if not expenses:
            return "Витрат ще немає."

        total = sum(e.amount for e in expenses)
        return f"💰 Загалом: {total:.0f} грн"


def delete_expense(expense_id: int):
    with Session() as session:
        exp = session.query(Expense).get(expense_id)
        if exp:
            session.delete(exp)
            session.commit()
            return True
        return False


def update_expense_amount(expense_id: int, new_amount: float):
    with Session() as session:
        exp = session.query(Expense).get(expense_id)
        if exp:
            exp.amount = new_amount
            session.commit()
            return True
        return False


# --- СКАРБНИЧКА ---

def create_goal(user_id: int, name: str, target: float):
    with Session() as session:
        new_goal = Goal(user_id=user_id, name=name, target_amount=target)
        session.add(new_goal)
        session.commit()
        return f"🎯 Ціль '{name}' на {target:.0f} грн створена!"


def get_all_goals(user_id: int):
    with Session() as session:
        return session.query(Goal).filter_by(user_id=user_id).all()


def get_goal_by_id(goal_id: int):
    with Session() as session:
        return session.query(Goal).get(goal_id)


def add_to_goal(goal_name: str, amount: float, description: str = "", user_id: int = None):
    with Session() as session:
        goal = session.query(Goal).filter_by(user_id=user_id, name=goal_name).first()
        if goal:
            goal.current_amount += amount
            history = GoalHistory(goal_id=goal.id, amount=amount, description=description)
            session.add(history)
            session.commit()
            return f"✅ Додано {amount:.0f} грн до '{goal_name}'"
        return "❌ Ціль не знайдена."


def get_goal_history(goal_id: int):
    with Session() as session:
        return session.query(GoalHistory).filter_by(goal_id=goal_id).order_by(GoalHistory.created_at.desc()).all()


def delete_goal(goal_id: int):
    with Session() as session:
        goal = session.query(Goal).get(goal_id)
        if goal:
            session.delete(goal)
            session.commit()
            return True
        return False


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