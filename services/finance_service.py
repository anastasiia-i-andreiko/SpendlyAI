from database.session import Session
from database.models import Expense, Goal, GoalHistory

def add_expense(amount: float, category: str, description: str = ""):
    with Session() as session:
        new_exp = Expense(amount=amount, category=category, description=description)
        session.add(new_exp)
        session.commit()

def get_expense_report():
    with Session() as session:
        expenses = session.query(Expense).all()
        if not expenses:
            return "Витрат ще немає."
        total = sum(e.amount for e in expenses)
        return f"📊 Твій звіт:\n💰 Загалом: {total:.0f} грн"

def create_goal(name: str, target: float):
    with Session() as session:
        new_goal = Goal(name=name, target_amount=target)
        session.add(new_goal)
        session.commit()
        return f"🎯 Ціль '{name}' створена!"

def add_to_goal(goal_name: str, amount: float):
    with Session() as session:
        goal = session.query(Goal).filter_by(name=goal_name).first()
        if goal:
            goal.current_amount += amount
            session.commit()
            return f"✅ Додано {amount} грн до '{goal_name}'"
        return "❌ Ціль не знайдена."
