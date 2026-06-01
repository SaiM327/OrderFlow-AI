import json

from ai_parser import parse_customer_message
from database import SessionLocal
from models import Order, OrderItem


def load_restaurant_info():
    with open("restaurant_info.json", "r") as f:
        return json.load(f)


def find_menu_item(item_name, menu):
    """
    Finds an exact menu item by name.
    The AI should already normalize item names, but this validates it.
    """
    for item in menu:
        if item["name"].lower() == item_name.lower():
            return item

    return None


def format_menu(menu):
    lines = ["Here is our menu:"]

    for item in menu:
        lines.append(f"- {item['name']}: ${item['price']:.2f}")

    return "\n".join(lines)


def format_dietary_options(menu, dietary_preference):
    matching_items = []

    for item in menu:
        tags = item.get("tags", [])

        if dietary_preference in tags:
            matching_items.append(item)

    if not matching_items:
        return f"Sorry, we do not currently have any {dietary_preference} options."

    lines = [f"Here are our {dietary_preference} options:"]

    for item in matching_items:
        lines.append(f"- {item['name']}: ${item['price']:.2f}")

    return "\n".join(lines)


def format_hours(hours):
    lines = ["Here are our hours:"]

    for day, time_range in hours.items():
        lines.append(f"- {day.capitalize()}: {time_range}")

    return "\n".join(lines)


def create_order(customer_phone, parsed, restaurant_info):
    menu = restaurant_info["menu"]
    parsed_items = parsed.get("items") or []

    if not parsed_items:
        return "I understood that you want to order, but I could not identify the items. Can you repeat your order?"

    db = SessionLocal()

    try:
        order = Order(
            customer_phone=customer_phone,
            status="confirmed",
            total_price=0.0
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        total = 0.0
        confirmation_lines = [f"Got it — I created order #{order.id}:"]

        for parsed_item in parsed_items:
            item_name = parsed_item.get("name")
            quantity = parsed_item.get("quantity", 1)
            modifications = parsed_item.get("modifications", "")

            menu_item = find_menu_item(item_name, menu)

            if menu_item is None:
                db.rollback()
                return f"Sorry, I could not find '{item_name}' on the menu."

            unit_price = float(menu_item["price"])
            line_total = unit_price * quantity
            total += line_total

            order_item = OrderItem(
                order_id=order.id,
                item_name=menu_item["name"],
                quantity=quantity,
                unit_price=unit_price,
                modifications=modifications
            )

            db.add(order_item)

            if modifications:
                confirmation_lines.append(
                    f"- {quantity}x {menu_item['name']} ({modifications}) — ${line_total:.2f}"
                )
            else:
                confirmation_lines.append(
                    f"- {quantity}x {menu_item['name']} — ${line_total:.2f}"
                )

        order.total_price = total
        db.commit()

        confirmation_lines.append(f"Total: ${total:.2f}")
        confirmation_lines.append("Payment is handled in-store.")

        return "\n".join(confirmation_lines)

    finally:
        db.close()


def handle_customer_message(customer_phone, message):
    restaurant_info = load_restaurant_info()

    parsed = parse_customer_message(message, restaurant_info)

    intent = parsed.get("intent")
    menu = restaurant_info["menu"]
    hours = restaurant_info.get("hours", {})

    if intent == "ask_menu":
        return format_menu(menu)

    if intent == "ask_dietary_options":
        dietary_preference = parsed.get("dietary_preference")

        if not dietary_preference:
            return "What dietary preference are you looking for? For example: vegan, vegetarian, or gluten-free."

        return format_dietary_options(menu, dietary_preference)

    if intent == "ask_hours":
        return format_hours(hours)

    if intent == "place_order":
        return create_order(customer_phone, parsed, restaurant_info)

    return "Sorry, I couldn't understand that. You can ask about our menu, hours, dietary options, or place an order."