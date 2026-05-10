from database.session import SessionLocal
from database.models import Expense, SavingsGoal, SavingsHistory
from sqlalchemy import func


# ── ВИТРАТИ ────────────────────────────────────────────

def add_expense(amount: float, category: str, description: str = "") -> str:
    with SessionLocal() as session:
        session.add(Expense(amount=amount, category=category, description=description))
        session.commit()
    return f"✅ Записано: {amount} грн — {category}"


def get_all_expenses():
    with SessionLocal() as session:
        return session.query(Expense).order_by(Expense.created_at.desc()).limit(15).all()


def delete_expense(exp_id: int) -> bool:
    with SessionLocal() as session:
        exp = session.query(Expense).get(exp_id)
        if exp:
            session.delete(exp)
            session.commit()
            return True
    return False


def update_expense_amount(exp_id: int, new_amount: float) -> bool:
    with SessionLocal() as session:
        exp = session.query(Expense).get(exp_id)
        if exp:
            exp.amount = new_amount
            session.commit()
            return True
    return False


def get_expense_report() -> str:
    with SessionLocal() as session:
        stats = session.query(
            Expense.category, func.sum(Expense.amount)
        ).group_by(Expense.category).all()
    if not stats:
        return "Витрат ще немає."
    total = sum(amt for _, amt in stats)
    lines = "\n".join(f"• {cat}: {amt:.0f} грн" for cat, amt in stats)
    return f"{lines}\n\n💰 Разом: {total:.0f} грн"


# ── СКАРБНИЧКА ─────────────────────────────────────────

def create_goal(name: str, target: float) -> str:
    with SessionLocal() as session:
        existing = session.query(SavingsGoal).filter(
            SavingsGoal.name.ilike(name)
        ).first()
        if existing:
            return "❌ Така ціль вже є."
        session.add(SavingsGoal(name=name, target_amount=target))
        session.commit()
    return f"🎯 Ціль «{name}» створена! Ціль: {target:.0f} грн"


def add_to_goal(name: str, amount: float, description: str = "") -> str:
    with SessionLocal() as session:
        goal = session.query(SavingsGoal).filter(
            SavingsGoal.name.ilike(f"%{name}%")
        ).first()
        if not goal:
            return f"❌ Ціль «{name}» не знайдена. Спочатку створи її кнопкою 🎯"
        goal.current_amount += amount
        session.add(SavingsHistory(
            goal_id=goal.id, amount=amount, description=description
        ))
        session.commit()
        left = goal.target_amount - goal.current_amount
        pct = (goal.current_amount / goal.target_amount * 100) if goal.target_amount else 0
        return (
            f"💰 Додано {amount:.0f} грн до «{goal.name}»\n"
            f"Прогрес: {goal.current_amount:.0f} / {goal.target_amount:.0f} грн ({pct:.1f}%)\n"
            f"Залишилось: {max(0, left):.0f} грн"
        )


def get_all_goals():
    with SessionLocal() as session:
        return session.query(SavingsGoal).all()


def get_goal_by_id(goal_id: int):
    with SessionLocal() as session:
        return session.query(SavingsGoal).get(goal_id)


def get_goal_history(goal_id: int):
    with SessionLocal() as session:
        return session.query(SavingsHistory).filter(
            SavingsHistory.goal_id == goal_id
        ).order_by(SavingsHistory.created_at.desc()).all()


def delete_history_record(record_id: int) -> bool:
    with SessionLocal() as session:
        rec = session.query(SavingsHistory).get(record_id)
        if rec:
            goal = session.query(SavingsGoal).get(rec.goal_id)
            if goal:
                goal.current_amount -= rec.amount
            session.delete(rec)
            session.commit()
            return True
    return False


def delete_goal(goal_id: int) -> bool:
    with SessionLocal() as session:
        goal = session.query(SavingsGoal).get(goal_id)
        if goal:
            session.delete(goal)
            session.commit()
            return True
    return False
