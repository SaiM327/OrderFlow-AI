import json
from ai_parser import parse_customer_message

with open("restaurant_info.json", "r") as f:
    restaurant_info = json.load(f)

messages = [
    "What vegan options do you have?",
    "Can I get 2 vegan bowls?",
    "Are you open on Sunday?",
    "Can I see the menu?",
    "I want a chicken sandwich with no mayo"
]

for message in messages:
    print("\nUSER:", message)
    parsed = parse_customer_message(message, restaurant_info)
    print(json.dumps(parsed, indent=2))