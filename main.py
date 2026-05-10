import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import config
from database.base import Base
from database.session import engine
from services.ai_service import AIService
from services.finance_service import (
    get_all_expenses, delete_expense, update_expense_amount,
    get_expense_report,
    create_goal, add_to_goal,
    get_all_goals, get_goal_by_id, get_goal_history,
    delete_history_record, delete_goal,
)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
ai = AIService()


# ── FSM ────────────────────────────────────────────────

class EditExpense(StatesGroup):
    waiting_new_amount = State()

class CreateGoal(StatesGroup):
    waiting_name = State()
    waiting_target = State()

class AddToGoal(StatesGroup):
    waiting_amount = State()


# ── МЕНЮ ───────────────────────────────────────────────

def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.row(
        types.KeyboardButton(text="💰 Скарбничка"),
        types.KeyboardButton(text="📊 Витрати"),
    )
    kb.row(
        types.KeyboardButton(text="🎯 Нова ціль"),
        types.KeyboardButton(text="❓ Допомога"),
    )
    return kb.as_markup(resize_keyboard=True)


# ── START ──────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 *Spendly AI* — твій фінансовий помічник!\n\n"
        "📝 *Як користуватись:*\n"
        "• Пиши: _'Купила каву 60'_ — запишу витрату\n"
        "• Пиши: _'Відклала 500 на машину'_ — додам до скарбнички\n"
        "• Кнопки нижче — для перегляду та управління\n\n"
        "Почнімо! 💪",
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


# ── ДОПОМОГА ───────────────────────────────────────────

@dp.message(F.text == "❓ Допомога")
async def help_cmd(message: types.Message):
    await message.answer(
        "📖 *Як користуватись Spendly:*\n\n"
        "*Витрати:*\n"
        "Просто напиши що і скільки:\n"
        "_'кава 45'_, _'таксі 200'_, _'купила сукню 1500'_\n\n"
        "*Скарбничка:*\n"
        "Спочатку створи ціль кнопкою 🎯, потім відкладай:\n"
        "_'відклала 300 на машину'_\n\n"
        "*Кнопки в звітах:*\n"
        "✏️ — змінити суму\n"
        "🗑 — видалити запис\n"
        "➕ — додати внесок до цілі\n"
        "⬅️ — назад",
        parse_mode="Markdown",
    )


# ── ВИТРАТИ ────────────────────────────────────────────

@dp.message(F.text == "📊 Витрати")
async def show_expenses(message: types.Message):
    report = get_expense_report()
    exps = get_all_expenses()

    if not exps:
        await message.answer("📭 Витрат ще немає.\nПросто напиши: _'кава 45'_", parse_mode="Markdown")
        return

    kb = InlineKeyboardBuilder()
    text = f"📊 *Звіт по витратах:*\n{report}\n\n*Деталі (натисни для дій):*\n"
    for e in exps:
        time_str = e.created_at.strftime("%d.%m %H:%M")
        desc = f" — {e.description}" if e.description else ""
        text += f"• {e.amount:.0f} грн | {e.category}{desc} | {time_str}\n"
        kb.row(
            types.InlineKeyboardButton(text=f"✏️ {e.amount:.0f}", callback_data=f"editexp_{e.id}"),
            types.InlineKeyboardButton(text="🗑", callback_data=f"delexp_{e.id}"),
        )

    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("delexp_"))
async def del_expense(callback: types.CallbackQuery):
    exp_id = int(callback.data.split("_")[1])
    if delete_expense(exp_id):
        await callback.answer("Видалено ✅")
        await show_expenses(callback.message)
    else:
        await callback.answer("Помилка")


@dp.callback_query(F.data.startswith("editexp_"))
async def edit_expense_start(callback: types.CallbackQuery, state: FSMContext):
    exp_id = int(callback.data.split("_")[1])
    await state.update_data(exp_id=exp_id)
    await state.set_state(EditExpense.waiting_new_amount)
    await callback.message.answer("✏️ Введи нову суму:")
    await callback.answer()


@dp.message(EditExpense.waiting_new_amount)
async def edit_expense_done(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        data = await state.get_data()
        if update_expense_amount(data["exp_id"], amount):
            await message.answer(f"✅ Суму змінено на {amount:.0f} грн")
        else:
            await message.answer("❌ Не знайдено.")
        await state.clear()
    except ValueError:
        await message.answer("Введи число.")


# ── СКАРБНИЧКА ─────────────────────────────────────────

@dp.message(F.text == "💰 Скарбничка")
async def show_savings(message: types.Message):
    goals = get_all_goals()
    if not goals:
        await message.answer(
            "🐖 Скарбничка порожня.\nНатисни *🎯 Нова ціль*, щоб почати накопичувати!",
            parse_mode="Markdown",
        )
        return

    kb = InlineKeyboardBuilder()
    text = "💰 *Твої цілі:*\n\n"
    for g in goals:
        pct = (g.current_amount / g.target_amount * 100) if g.target_amount else 0
        bar = "▓" * int(pct / 10) + "░" * (10 - int(pct / 10))
        text += f"*{g.name}*\n{bar} {pct:.0f}%\n{g.current_amount:.0f} / {g.target_amount:.0f} грн\n\n"
        kb.row(types.InlineKeyboardButton(text=f"⚙️ {g.name}", callback_data=f"goal_{g.id}"))

    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("goal_"))
async def show_goal_detail(callback: types.CallbackQuery):
    goal_id = int(callback.data.split("_")[1])
    goal = get_goal_by_id(goal_id)
    history = get_goal_history(goal_id)

    pct = (goal.current_amount / goal.target_amount * 100) if goal.target_amount else 0
    text = (
        f"🎯 *{goal.name}*\n"
        f"💰 {goal.current_amount:.0f} / {goal.target_amount:.0f} грн ({pct:.1f}%)\n\n"
        f"🕰 *Останні внески:*\n"
    )

    kb = InlineKeyboardBuilder()
    if history:
        for h in history[:8]:
            time_str = h.created_at.strftime("%d.%m %H:%M")
            desc = f" — {h.description}" if h.description else ""
            text += f"• {h.amount:.0f} грн | {time_str}{desc}\n"
            kb.row(types.InlineKeyboardButton(
                text=f"🗑 {h.amount:.0f} грн", callback_data=f"delrec_{h.id}"
            ))
    else:
        text += "_Внесків ще немає_\n"

    kb.row(types.InlineKeyboardButton(text="➕ Додати внесок", callback_data=f"addsave_{goal_id}"))
    kb.row(types.InlineKeyboardButton(text="🗑 Видалити ціль", callback_data=f"delgoal_{goal_id}"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_savings"))

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data == "back_savings")
async def back_to_savings(callback: types.CallbackQuery):
    await show_savings(callback.message)


@dp.callback_query(F.data.startswith("delrec_"))
async def del_record(callback: types.CallbackQuery):
    rec_id = int(callback.data.split("_")[1])
    if delete_history_record(rec_id):
        await callback.answer("Видалено ✅")
        await show_savings(callback.message)
    else:
        await callback.answer("Помилка")


@dp.callback_query(F.data.startswith("delgoal_"))
async def del_goal_cb(callback: types.CallbackQuery):
    goal_id = int(callback.data.split("_")[1])
    if delete_goal(goal_id):
        await callback.answer("Ціль видалена")
        await show_savings(callback.message)
    else:
        await callback.answer("Помилка")


@dp.callback_query(F.data.startswith("addsave_"))
async def add_save_start(callback: types.CallbackQuery, state: FSMContext):
    goal_id = int(callback.data.split("_")[1])
    await state.update_data(goal_id=goal_id)
    await state.set_state(AddToGoal.waiting_amount)
    await callback.message.answer("💵 Введи суму внеску (можна з коментарем, напр. _'500 з зарплати'_):", parse_mode="Markdown")
    await callback.answer()


@dp.message(AddToGoal.waiting_amount)
async def add_save_done(message: types.Message, state: FSMContext):
    parts = message.text.split(maxsplit=1)
    try:
        amount = float(parts[0].replace(",", "."))
        desc = parts[1] if len(parts) > 1 else ""
        data = await state.get_data()
        goal = get_goal_by_id(data["goal_id"])
        result = add_to_goal(goal.name, amount, desc)
        await message.answer(result)
        await state.clear()
        await show_savings(message)
    except (ValueError, IndexError):
        await message.answer("Введи число, наприклад: _'500'_ або _'500 з зарплати'_", parse_mode="Markdown")


# ── НОВА ЦІЛЬ ──────────────────────────────────────────

@dp.message(F.text == "🎯 Нова ціль")
async def new_goal_start(message: types.Message, state: FSMContext):
    await state.set_state(CreateGoal.waiting_name)
    await message.answer("✍️ Як назвемо ціль? (напр. _Машина_, _iPhone_, _Відпустка_)", parse_mode="Markdown")


@dp.message(CreateGoal.waiting_name)
async def new_goal_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(CreateGoal.waiting_target)
    await message.answer(f"💰 Скільки хочеш зібрати на *{message.text}*?", parse_mode="Markdown")


@dp.message(CreateGoal.waiting_target)
async def new_goal_target(message: types.Message, state: FSMContext):
    try:
        target = float(message.text.replace(",", "."))
        data = await state.get_data()
        result = create_goal(data["name"], target)
        await message.answer(result)
        await state.clear()
    except ValueError:
        await message.answer("Введи число.")


# ── ШІ (будь-який текст) ───────────────────────────────

MENU_BUTTONS = {"💰 Скарбничка", "📊 Витрати", "🎯 Нова ціль", "❓ Допомога"}


@dp.message(F.text)
async def ai_handler(message: types.Message):
    if message.text in MENU_BUTTONS:
        return
    await bot.send_chat_action(message.chat.id, "typing")
    result = await ai.chat_with_user(message.text)
    await message.answer(result)


# ── ЗАПУСК ─────────────────────────────────────────────

async def main():
    Base.metadata.create_all(bind=engine)
    print("🚀 Spendly AI запущено!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())