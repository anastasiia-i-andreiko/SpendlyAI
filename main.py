import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import config
from database.base import Base
from database.session import engine
from services.ai_service import AIService
from services.finance_service import get_expense_report

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
ai = AIService()

class AIChat(StatesGroup):
    waiting_question = State()

def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.row(types.KeyboardButton(text="💰 Скарбничка"), types.KeyboardButton(text="📊 Витрати"))
    kb.row(types.KeyboardButton(text="🤖 Спитати ШІ"))
    return kb.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    Base.metadata.create_all(bind=engine)
    await message.answer("👋 Бот запущений!", reply_markup=main_menu())

@dp.message(F.text == "📊 Витрати")
async def show_expenses(message: types.Message):
    report = get_expense_report(message.from_user.id)
    await message.answer(report)

@dp.message(F.text == "🤖 Спитати ШІ")
async def ask_ai(message: types.Message, state: FSMContext):
    await state.set_state(AIChat.waiting_question)
    await message.answer("Напиши витрату або запитання:")

@dp.message(AIChat.waiting_question)
async def ai_chat_process(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    # ОСЬ ТУТ ПЕРЕДАЄМО user_id
    res = await ai.chat_with_user(message.text, message.from_user.id)
    await message.answer(res)

@dp.message(F.text)
async def global_handler(message: types.Message):
    if message.text in ["💰 Скарбничка", "📊 Витрати", "🤖 Спитати ШІ"]: return
    await bot.send_chat_action(message.chat.id, "typing")
    # ОСЬ ТУТ ПЕРЕДАЄМО user_id
    res = await ai.chat_with_user(message.text, message.from_user.id)
    await message.answer(res)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
