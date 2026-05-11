import json
import groq
import config
from services import finance_service as fs

class AIService:
    def __init__(self):
        self.client = groq.Groq(api_key=config.GROQ_API_KEY)
        self.model = "llama3-70b-8192"

    async def chat_with_user(self, user_text: str):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_expense",
                    "description": "Записати витрату",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number"},
                            "category": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["amount", "category"]
                    }
                }
            }
        ]

        messages = [
            {"role": "system", "content": "Ти Spendly AI. Якщо бачиш витрату (напр. 'кава 60'), викликай add_expense. Відповідай коротко українською."},
            {"role": "user", "content": user_text}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        msg = response.choices[0].message
        if msg.tool_calls:
            for tool in msg.tool_calls:
                if tool.function.name == "add_expense":
                    args = json.loads(tool.function.arguments)
                    fs.add_expense(args['amount'], args['category'], args.get('description', ''))
                    return f"✅ Записано: {args['amount']} грн на {args['category']}."
        
        return msg.content
