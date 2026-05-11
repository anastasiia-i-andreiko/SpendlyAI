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


class AIChat(StatesGroup):
    waiting_question = State()


# ── МЕНЮ ───────────────────────────────────────────────

def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.row(
        types.KeyboardButton(text="💰 Скарбничка"),
        types.KeyboardButton(text="📊 Витрати"),
    )
    kb.row(
        types.KeyboardButton(text="🤖 Спитати ШІ"),
        types.KeyboardButton(text="🎯 Нова ціль"),
    )
    kb.row(
        types.KeyboardButton(text="❓ Допомога"),
    )
    return kb.as_markup(resize_keyboard=True)


# ── START ──────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 *Spendly AI* — твій приватний фінансовий помічник!\n\n"
        "🔒 *Твої дані бачиш тільки ти.*\n\n"
        "📝 *Як користуватись:*\n"
        "• Пиши: _'кава 60'_ — запишу витрату\n"
        "• Кнопка *🤖 Спитати ШІ* — для звичайних питань\n\n"
        "Почнімо! 💪",
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


# ── ШІ ЧАТ ─────────────────────────────────────────────

@dp.message(F.text == "🤖 Спитати ШІ")
async def ai_chat_start(message: types.Message, state: FSMContext):
    await state.set_state(AIChat.waiting_question)
    exit_kb = ReplyKeyboardBuilder().row(types.KeyboardButton(text="⬅️ Вийти з чату"))
    await message.answer(
        "🤖 *Режим чату з ШІ активовано.*\n"
        "Запитуй що завгодно про фінанси або просто поспілкуємось!",
        parse_mode="Markdown",
        reply_markup=exit_kb.as_markup(resize_keyboard=True)
    )


@dp.message(AIChat.waiting_question, F.text == "⬅️ Вийти з чату")
async def ai_chat_exit(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Повертаємось до управління бюджетом.", reply_markup=main_menu())


@dp.message(AIChat.waiting_question)
async def ai_chat_process(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    # Передаємо user_id, щоб ШІ знав, з ким говорить (якщо це реалізовано в сервісі)
    result = await ai.chat_with_user(message.text)
    await message.answer(result)


# ── ВИТРАТИ (Приватні) ──────────────────────────────────

@dp.message(F.text == "📊 Витрати")
async def show_expenses(message: types.Message):
    user_id = message.from_user.id
    report = get_expense_report(user_id=user_id)
    exps = get_all_expenses(user_id=user_id)

    if not exps:
        await message.answer("📭 У тебе ще немає витрат.", parse_mode="Markdown")
        return

    kb = InlineKeyboardBuilder()
    text = f"📊 *Твій звіт по витратах:*\n{report}\n\n*Дії:* \n"
    for e in exps[:10]:  # Обмежуємо список для зручності
        text += f"• {e.amount:.0f} грн | {e.category}\n"
        kb.row(
            types.InlineKeyboardButton(text=f"✏️ {e.amount:.0f}", callback_data=f"editexp_{e.id}"),
            types.InlineKeyboardButton(text="🗑", callback_data=f"delexp_{e.id}"),
        )

    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("delexp_"))
async def del_expense_cb(callback: types.CallbackQuery):
    exp_id = int(callback.data.split("_")[1])
    # Бажано додати перевірку в сервісі, чи належить exp_id цьому user_id
    if delete_expense(exp_id):
        await callback.answer("Видалено")
        await show_expenses(callback.message)
    else:
        await callback.answer("Помилка")


# ── СКАРБНИЧКА (Приватна) ───────────────────────────────

@dp.message(F.text == "💰 Скарбничка")
async def show_savings(message: types.Message):
    user_id = message.from_user.id
    goals = get_all_goals(user_id=user_id)

    if not goals:
        await message.answer("🐖 У тебе поки немає цілей.", parse_mode="Markdown")
        return

    kb = InlineKeyboardBuilder()
    text = "💰 *Твої цілі:*\n\n"
    for g in goals:
        pct = (g.current_amount / g.target_amount * 100) if g.target_amount else 0
        bar = "▓" * int(pct / 10) + "░" * (10 - int(pct / 10))
        text += f"*{g.name}*\n{bar} {pct:.0f}%\n{g.current_amount:.0f} / {g.target_amount:.0f} грн\n\n"
        kb.row(types.InlineKeyboardButton(text=f"⚙️ {g.name}", callback_data=f"goal_{g.id}"))

    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")


# ── НОВА ЦІЛЬ ──────────────────────────────────────────

@dp.message(F.text == "🎯 Нова ціль")
async def new_goal_start(message: types.Message, state: FSMContext):
    await state.set_state(CreateGoal.waiting_name)
    await message.answer("✍️ Як назвемо ціль?")


@dp.message(CreateGoal.waiting_name)
async def new_goal_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(CreateGoal.waiting_target)
    await message.answer(f"💰 Скільки треба зібрати на *{message.text}*?", parse_mode="Markdown")


@dp.message(CreateGoal.waiting_target)
async def new_goal_target(message: types.Message, state: FSMContext):
    try:
        target = float(message.text.replace(",", "."))
        data = await state.get_data()
        # Передаємо user_id при створенні
        result = create_goal(user_id=message.from_user.id, name=data["name"], target=target)
        await message.answer(result, reply_markup=main_menu())
        await state.clear()
    except ValueError:
        await message.answer("Введи число!")


# ── ОБРОБКА ТЕКСТУ (ШІ запис) ─────────────────────────

@dp.message(F.text)
async def ai_handler(message: types.Message):
    # Ігноруємо кнопки меню
    if message.text in {"💰 Скарбничка", "📊 Витрати", "🎯 Нова ціль", "❓ Допомога", "🤖 Спитати ШІ"}:
        return

    await bot.send_chat_action(message.chat.id, "typing")
    # ШІ повинен розуміти контекст додавання через сервіс з user_id
    result = await ai.chat_with_user(message.text, user_id=message.from_user.id)
    await message.answer(result)


# ── ЗАПУСК ─────────────────────────────────────────────

async def main():
    Base.metadata.create_all(bind=engine)
    print("🚀 Spendly AI запущено!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())