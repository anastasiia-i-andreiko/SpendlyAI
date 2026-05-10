import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    print("❌ ПОМИЛКА: BOT_TOKEN не знайдено в змінних оточення!")
if not GROQ_API_KEY:
    print("❌ ПОМИЛКА: GROQ_API_KEY не знайдено в змінних оточення!")
