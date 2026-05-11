import json
import re
from groq import AsyncGroq
import config
from services.finance_service import add_expense, add_to_goal
from services.prompts import SYSTEM_PROMPT

class AIService:
    def __init__(self):
        self.client = AsyncGroq(api_key=config.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    async def chat_with_user(self, user_text: str, user_id: int) -> str:
        try:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                ],
                temperature=0.1,
                max_tokens=300,
            )
            ai_res = completion.choices[0].message.content.strip()
            
            match = re.search(r"(?:JSON_DATA:\s*)?(\{.*\})", ai_res, re.DOTALL)
            if not match:
                return ai_res
            
            data = json.loads(match.group(1))
            
            if data.get("type") == "expense":
                return add_expense(
                    user_id=user_id, 
                    amount=float(data["amount"]),
                    category=data.get("category", "Інше"),
                    description=data.get("description", ""),
                )

            if data.get("type") == "save":
                goal_name = data.get("goal_name") or data.get("description") or "скарбничка"
                return add_to_goal(
                    user_id=user_id,
                    goal_name=goal_name,
                    amount=float(data["amount"]),
                    description=data.get("description", ""),
                )
            
            return ai_res
        except Exception:
            return ai_res # Якщо виникла помилка в JSON, просто повертаємо текст ШІ
