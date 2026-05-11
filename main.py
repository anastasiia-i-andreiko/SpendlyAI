import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import config
from services.ai_service import AIService
from services import finance_service as fs

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
ai = AIService()

class CreateGoal(StatesGroup):
    waiting_name = State()
    waiting_target = State()

def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.row(types.KeyboardButton(text="💰 Скарбничка"), types.KeyboardButton(text="📊 Витрати"))
    kb.row(types.KeyboardButton(text="🎯 Нова ціль"), types.KeyboardButton(text="❓ Допомога"))
    return kb.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привіт! Я Spendly AI. Пиши витрати, а я запишу.", reply_markup=main_menu())

@dp.message(F.text == "📊 Витрати")
async def show_expenses(message: types.Message):
    report = fs.get_expense_report()
    await message.answer(report)

@dp.message(F.text == "🎯 Нова ціль")
async def goal_start(message: types.Message, state: FSMContext):
    await state.set_state(CreateGoal.waiting_name)
    await message.answer("Назва цілі?")

@dp.message(CreateGoal.waiting_name)
async def goal_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(CreateGoal.waiting_target)
    await message.answer("Сума цілі?")

@dp.message(CreateGoal.waiting_target)
async def goal_target(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target = float(message.text.replace(",", "."))
    res = fs.create_goal(data['name'], target)
    await message.answer(res, reply_markup=main_menu())
    await state.clear()

@dp.message(F.text)
async def handle_text(message: types.Message):
    if message.text in ["💰 Скарбничка", "📊 Витрати", "🎯 Нова ціль"]: return
    res = await ai.chat_with_user(message.text)
    await message.answer(res)

async def main():
    print("🚀 Бот запущений")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
