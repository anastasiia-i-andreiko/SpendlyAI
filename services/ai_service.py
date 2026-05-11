import json
from groq import AsyncGroq
import config
from services.finance_service import add_expense, add_to_goal, get_expense_report

class AIService:
    def __init__(self):
        self.client = AsyncGroq(api_key=config.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    def _get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "add_expense",
                    "description": "Записати витрату користувача в базу даних",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {
                                "type": "number",
                                "description": "Сума витрати в гривнях"
                            },
                            "category": {
                                "type": "string",
                                "description": "Категорія: їжа, транспорт, розваги, одяг, інше"
                            },
                            "description": {
                                "type": "string",
                                "description": "Короткий опис витрати"
                            }
                        },
                        "required": ["amount", "category"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_to_goal",
                    "description": "Додати гроші до цілі накопичення",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "goal_name": {
                                "type": "string",
                                "description": "Назва цілі накопичення"
                            },
                            "amount": {
                                "type": "number",
                                "description": "Сума в гривнях"
                            },
                            "description": {
                                "type": "string",
                                "description": "Коментар до внеску"
                            }
                        },
                        "required": ["goal_name", "amount"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_expense_summary",
                    "description": "Показати зведення витрат користувача",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

    async def chat_with_user(self, user_text: str, user_id: int = None) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ти фінансовий помічник Spendly. "
                            "Якщо користувач згадує витрату — викликай add_expense. "
                            "Якщо відкладає на ціль — викликай add_to_goal. "
                            "Якщо питає про статистику чи витрати — викликай get_expense_summary. "
                            "Відповідай українською мовою, коротко і дружньо."
                        )
                    },
                    {"role": "user", "content": user_text}
                ],
                tools=self._get_tools(),
                tool_choice="auto",
                max_tokens=500
            )

            message = response.choices[0].message

            # Модель викликала інструмент
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                if func_name == "add_expense" and user_id:
                    return add_expense(
                        user_id=user_id,
                        amount=float(args["amount"]),
                        category=args.get("category", "інше"),
                        description=args.get("description", "")
                    )

                elif func_name == "add_to_goal" and user_id:
                    return add_to_goal(
                        name=args["goal_name"],
                        amount=float(args["amount"]),
                        description=args.get("description", ""),
                        user_id=user_id
                    )

                elif func_name == "get_expense_summary" and user_id:
                    return get_expense_report(user_id=user_id)

            # Просто текстова відповідь
            return message.content or "Не зрозуміла запит 🤔"

        except Exception as e:
            return f"❌ Помилка: {e}"