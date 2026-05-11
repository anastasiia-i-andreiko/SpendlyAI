from database.session import Session
from database.models import Expense, Goal, GoalHistory

def add_expense(user_id: int, amount: float, category: str, description: str = ""):
    with Session() as session:
        new_exp = Expense(user_id=user_id, amount=amount, category=category, description=description)
        session.add(new_exp)
        session.commit()
        return f"✅ Записано витрату: {amount:.0f} грн на '{category}'"

def add_to_goal(user_id: int, goal_name: str, amount: float, description: str = ""):
    with Session() as session:
        goal = session.query(Goal).filter_by(user_id=user_id, name=goal_name).first()
        if goal:
            goal.current_amount += amount
            history = GoalHistory(goal_id=goal.id, amount=amount, description=description)
            session.add(history)
            session.commit()
            return f"✅ Додано {amount:.0f} грн до цілі '{goal_name}'"
        return f"❌ Ціль '{goal_name}' не знайдена."

def get_expense_report(user_id: int):
    with Session() as session:
        expenses = session.query(Expense).filter_by(user_id=user_id).all()
        if not expenses: return "Витрат ще немає."
        total = sum(e.amount for e in expenses)
        return f"💰 Загалом витрачено: {total:.0f} грн"

def create_goal(user_id: int, name: str, target: float):
    with Session() as session:
        new_goal = Goal(user_id=user_id, name=name, target_amount=target)
        session.add(new_goal)
        session.commit()
        return f"🎯 Ціль '{name}' створена!"
