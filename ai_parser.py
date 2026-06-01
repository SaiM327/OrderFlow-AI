import json
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def parse_customer_message(message: str, restaurant_info: dict) -> dict:
    prompt = f"""
You are an AI parser for a restaurant WhatsApp bot.

Convert the customer's message into structured JSON.

Restaurant info:
{json.dumps(restaurant_info, indent=2)}

Possible intents:
- ask_hours
- ask_menu
- ask_dietary_options
- place_order
- unknown

Return ONLY valid JSON in this exact format:

{{
  "intent": "place_order",
  "items": [
    {{
      "name": "Vegan Bowl",
      "quantity": 2,
      "modifications": ""
    }}
  ],
  "dietary_preference": null,
  "question": null
}}

Rules:
- If the user asks for vegan/vegetarian/gluten-free options, use "ask_dietary_options".
- If the user asks about hours/opening/closing, use "ask_hours".
- If the user asks to see the menu, use "ask_menu".
- If the user wants to order food, use "place_order".
- If the item name is close to a real menu item, use the exact menu item name from the restaurant menu.
- If unclear, use "unknown".
- Return JSON only. No markdown. No explanation.

Customer message:
{message}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    raw_text = response.choices[0].message.content

    return json.loads(raw_text)