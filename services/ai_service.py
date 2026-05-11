import json
import groq
import config
from services import finance_service as fs

class AIService:
    def __init__(self):
        self.client = groq.Groq(api_key=config.GROQ_API_KEY)
        self.model = "llama3-70b-8192"

    async def chat_with_user(self, user_text: str, user_id: int):
        # Описуємо інструменти (функції), які ШІ може викликати
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_expense",
                    "description": "Записати витрату грошей",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number", "description": "Сума витрати"},
                            "category": {"type": "string", "description": "Категорія (напр. Кава, Продукти, Таксі)"},
                            "description": {"type": "string", "description": "Опис витрати"}
                        },
                        "required": ["amount", "category"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_to_goal",
                    "description": "Додати гроші в скарбничку на конкретну ціль",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "goal_name": {"type": "string", "description": "Назва цілі (напр. Машина, iPhone)"},
                            "amount": {"type": "number", "description": "Сума внеску"},
                            "description": {"type": "string", "description": "Коментар до внеску"}
                        },
                        "required": ["goal_name", "amount"]
                    }
                }
            }
        ]

        # Формуємо запит до Groq
        messages = [
            {"role": "system", "content": "Ти — Spendly AI, фінансовий помічник. Твоє завдання — розпізнавати витрати та внески в скарбничку. Якщо користувач пише щось на кшталт 'кава 60' або 'відклала 100 на машину', ти ПОВИНЕН викликати відповідну функцію. Будь лаконічним, відповідай українською."},
            {"role": "user", "content": user_text}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # Якщо ШІ вирішив викликати функцію
        if tool_calls:
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                if function_name == "add_expense":
                    fs.add_expense(
                        user_id=user_id,
                        amount=args.get("amount"),
                        category=args.get("category"),
                        description=args.get("description", "")
                    )
                    return f"✅ Записав витрату: {args.get('amount')} грн на {args.get('category')}."

                elif function_name == "add_to_goal":
                    result = fs.add_to_goal(
                        user_id=user_id,
                        goal_name=args.get("goal_name"),
                        amount=args.get("amount"),
                        description=args.get("description", "")
                    )
                    return result
        
        # Якщо це просто текст (балачки)
        return response_message.content
