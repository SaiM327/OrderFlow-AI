import json
import os
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _parse_json_response(raw_text: str) -> dict:
    if not raw_text or not raw_text.strip():
        return {"intent": "unknown"}

    text = raw_text.strip()

    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"intent": "unknown"}


def parse_customer_message(
    message: str, restaurant_info: dict, awaiting_name: bool = False
) -> dict:
    categories = restaurant_info.get("categories", [])

    context_note = ""
    if awaiting_name:
        context_note = (
            "\nContext: The customer was just asked for their name. "
            'A short reply that looks like a person\'s name should be treated as "provide_name" '
            'with "customer_name" set. Only choose a different intent if the message is clearly '
            "something else (e.g. a menu request or an order).\n"
        )

    prompt = f"""
You are an AI parser for a restaurant WhatsApp bot.

Convert the customer's message into structured JSON.
{context_note}

Restaurant info:
{json.dumps(restaurant_info, indent=2)}

Menu categories: {", ".join(categories)}

Possible intents:
- greeting
- provide_name
- ask_hours
- ask_menu
- ask_menu_category
- ask_dietary_options
- add_to_order
- add_all_to_order
- remove_from_cart
- update_quantity
- view_cart
- clear_cart
- checkout
- cancel_order
- call_restaurant
- unknown

Return ONLY valid JSON in this exact format:

{{
  "intent": "add_to_order",
  "items": [
    {{
      "name": "Carne Asada Burrito",
      "quantity": 1,
      "modifications": ""
    }}
  ],
  "category": null,
  "dietary_preference": null,
  "customer_name": null
}}

Rules:
- If the user greets you (e.g. "hi", "hello", "hey", "good morning"), use "greeting".
- If the user shares their name (e.g. "I'm Alex", "my name is Alex", "call me Alex", or a short name-only reply like "Alex" or "sai"), use "provide_name" and set "customer_name".
- A single-word or short reply that looks like a person's name (not a menu item) should be treated as "provide_name".
- If the user asks for vegan/vegetarian/gluten-free options, use "ask_dietary_options".
- If the user asks about hours/opening/closing, use "ask_hours".
- If the user asks to see the menu in general (e.g. "menu", "what do you have"), use "ask_menu".
- If the user wants to start ordering but hasn't picked items yet (e.g. "can I order", "I want to order", "I'd like to get something", "I'm hungry"), use "ask_menu".
- If the user asks to see a specific category (e.g. "appetizers", "show me drinks", "entrees"), use "ask_menu_category" and set "category" to one of: {", ".join(categories)}.
- If the user wants to add item(s) to their order (e.g. "add 1 burrito", "I'll take 2 horchatas"), use "add_to_order".
- If the user wants to add every/all menu items (e.g. "add everything", "add all items on the menu"), use "add_all_to_order" with an empty items list.
- If the user wants to remove item(s) from their cart (e.g. "remove the burrito", "take off the horchata"), use "remove_from_cart".
- If the user wants to change how many of an item they have (e.g. "change burrito to 2", "make it 3 tacos"), use "update_quantity".
- If the user wants to see their current order/cart (e.g. "what's in my order", "show my cart"), use "view_cart".
- If the user wants to empty their cart and start over (e.g. "clear my cart", "start over", "empty my order"), use "clear_cart".
- If the user is done ordering (e.g. "checkout", "that's all", "place my order", "I'm done"), use "checkout".
- If the user wants to cancel a recently placed order (e.g. "cancel order", "cancel my order", "never mind"), use "cancel_order".
- If the user wants to call the restaurant or speak to a person instead of using the bot (e.g. "call the restaurant", "phone number", "speak to someone"), use "call_restaurant".
- For add_to_order, remove_from_cart, update_quantity, and ask_menu_category, use exact menu item names and category names from the restaurant info.
- For remove_from_cart, include quantity if the user specifies how many to remove (e.g. "remove 1 burrito" -> quantity 1). Otherwise omit quantity or set to null.
- For update_quantity, set the item quantity to the new total the user wants.
- Normalize category names to match exactly: {", ".join(categories)} (e.g. "desert"/"dessert" -> "desserts", "appetizer" -> "appetizers").
- If the item name is close to a real menu item, use the exact menu item name.
- If unclear, use "unknown".
- Return JSON only. No markdown. No explanation.

Customer message:
{message}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        raw_text = response.choices[0].message.content
        return _parse_json_response(raw_text)
    except Exception:
        return {"intent": "unknown"}
