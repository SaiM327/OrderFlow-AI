from bot import handle_customer_message


messages = [
    "Can I see the menu?",
    "What vegan options do you have?",
    "Are you open on Sunday?",
    "Can I get 2 vegan bowls?",
    "I want a chicken sandwich with no mayo"
]


for message in messages:
    print("\nCUSTOMER:", message)

    response = handle_customer_message(
        customer_phone="+15551234567",
        message=message
    )

    print("BOT:")
    print(response)