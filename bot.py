import json
from datetime import datetime, timedelta

from ai_parser import parse_customer_message
from database import SessionLocal
from models import Order, OrderItem


AWAITING_NAME = "awaiting_name"
BUILDING_ORDER_TIMEOUT_MINUTES = 60
CANCEL_ORDER_WINDOW_MINUTES = 5

CANCEL_ORDER_PHRASES = (
    "cancel order",
    "cancel my order",
    "cancel the order",
    "never mind",
    "nevermind",
)

CALL_RESTAURANT_PHRASES = (
    "call restaurant",
    "call the restaurant",
    "phone number",
    "speak to someone",
    "speak to a person",
    "talk to someone",
    "talk to a person",
    "real person",
    "human",
)

CATEGORY_ALIASES = {
    "appetizer": "appetizers",
    "entree": "entrees",
    "drink": "drinks",
    "dessert": "desserts",
    "desert": "desserts",
    "side": "sides",
}

GREETING_PHRASES = {
    "hi",
    "hello",
    "hey",
    "hiya",
    "yo",
    "good morning",
    "good afternoon",
    "good evening",
}

MENU_PHRASES = (
    "menu",
    "show menu",
    "see menu",
    "the menu",
    "what's the menu",
    "whats the menu",
    "what do you have",
    "what do you serve",
    "what can i get",
)

ORDER_START_PHRASES = (
    "can i order",
    "could i order",
    "i want to order",
    "i'd like to order",
    "id like to order",
    "i would like to order",
    "place an order",
    "make an order",
    "start an order",
    "start ordering",
    "order food",
    "order something",
    "get something to eat",
    "i want food",
    "i'm hungry",
    "im hungry",
    "can i get something",
    "i want to get",
    "i'd like to get",
    "id like to get",
    "can i get",
    "i'll have",
    "ill have",
)

CHECKOUT_PHRASES = (
    "checkout",
    "check out",
    "that's all",
    "thats all",
    "that is all",
    "place my order",
    "submit order",
    "finish order",
    "i'm done",
    "im done",
    "done ordering",
    "ready to checkout",
)

CART_PHRASES = (
    "my cart",
    "my order",
    "view cart",
    "show cart",
    "what's in my cart",
    "whats in my cart",
    "what did i order",
    "show my order",
    "see my cart",
    "current cart",
    "current order",
)

HOURS_PHRASES = (
    "hours",
    "what are your hours",
    "what are the hours",
    "when are you open",
    "are you open",
    "opening hours",
)


def load_restaurant_info():
    with open("restaurant_info.json", "r") as f:
        return json.load(f)


def normalize_category(category, categories):
    if not category:
        return None

    cat = category.lower().strip()
    cat = CATEGORY_ALIASES.get(cat, cat)

    for valid in categories:
        if valid.lower() == cat:
            return valid

    return None


def find_menu_item(item_name, menu):
    for item in menu:
        if item["name"].lower() == item_name.lower():
            return item

    return None


def format_category_prompt(categories):
    lines = ["What would you like to see? Pick a category:"]

    for category in categories:
        lines.append(f"- {category.capitalize()}")

    lines.append("")
    lines.append("Browse the categories and add whatever you'd like.")
    lines.append("Say checkout when you're ready to place your order.")

    return "\n".join(lines)


def format_category_menu(category, menu):
    items = [
        item
        for item in menu
        if item.get("category") == category and item.get("available", True)
    ]

    if not items:
        return f"Sorry, nothing is available in {category} right now."

    lines = [f"{category.capitalize()}:"]

    for item in items:
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


def get_customer_name(db, customer_phone):
    building_order = (
        db.query(Order)
        .filter(Order.customer_phone == customer_phone, Order.status == "building")
        .first()
    )

    if building_order and building_order.customer_name:
        return building_order.customer_name

    recent_order = (
        db.query(Order)
        .filter(
            Order.customer_phone == customer_phone,
            Order.customer_name.isnot(None),
        )
        .order_by(Order.created_at.desc())
        .first()
    )

    if recent_order:
        return recent_order.customer_name

    return None


def normalize_name(name):
    return " ".join(part.capitalize() for part in name.strip().split())


def is_awaiting_name(db, customer_phone):
    order = (
        db.query(Order)
        .filter(Order.customer_phone == customer_phone, Order.status == "building")
        .first()
    )

    return order is not None and order.special_notes == AWAITING_NAME


def set_awaiting_name(customer_phone):
    db = SessionLocal()

    try:
        order = get_or_create_building_order(db, customer_phone)
        order.special_notes = AWAITING_NAME
        db.commit()
    finally:
        db.close()


def clear_awaiting_name(customer_phone):
    db = SessionLocal()

    try:
        order = (
            db.query(Order)
            .filter(Order.customer_phone == customer_phone, Order.status == "building")
            .first()
        )

        if order and order.special_notes == AWAITING_NAME:
            order.special_notes = None
            db.commit()
    finally:
        db.close()


def expire_stale_building_orders(db):
    cutoff = datetime.utcnow() - timedelta(minutes=BUILDING_ORDER_TIMEOUT_MINUTES)

    stale_orders = (
        db.query(Order)
        .filter(Order.status == "building", Order.created_at < cutoff)
        .all()
    )

    for order in stale_orders:
        order.status = "abandoned"

    if stale_orders:
        db.commit()


def get_building_order(db, customer_phone):
    return (
        db.query(Order)
        .filter(Order.customer_phone == customer_phone, Order.status == "building")
        .first()
    )


def get_or_create_building_order(db, customer_phone):
    expire_stale_building_orders(db)

    order = get_building_order(db, customer_phone)

    if order is None:
        order = Order(
            customer_phone=customer_phone,
            customer_name=get_customer_name(db, customer_phone),
            status="building",
            total_price=0.0,
        )
        db.add(order)
        db.commit()
        db.refresh(order)

    return order


def save_customer_name(customer_phone, name, restaurant_info=None):
    db = SessionLocal()

    try:
        order = get_or_create_building_order(db, customer_phone)
        order.customer_name = normalize_name(name)

        if order.special_notes == AWAITING_NAME:
            order.special_notes = None

        has_items = len(order.items) > 0
        saved_name = order.customer_name
        db.commit()
    finally:
        db.close()

    if has_items and restaurant_info is not None:
        return checkout_order(customer_phone, restaurant_info)

    return (
        f"Nice to meet you, {saved_name}! "
        "You can browse the menu, ask about hours, or start adding items whenever you're ready."
    )


def handle_greeting(customer_phone, restaurant_info):
    db = SessionLocal()

    try:
        name = get_customer_name(db, customer_phone)
        restaurant_name = restaurant_info["restaurant_name"]

        if name:
            return (
                f"Hi {name}! Welcome back to {restaurant_name}. "
                "You can browse the menu, ask about hours, or start adding items whenever you're ready. "
                "Prefer to call? Just say call restaurant."
            )

        set_awaiting_name(customer_phone)

        return (
            f"Hi! Welcome to {restaurant_name}. "
            "What's your name? (Or say call restaurant if you'd rather order by phone.)"
        )

    finally:
        db.close()


def recalculate_order_total(order):
    return sum(item.quantity * item.unit_price for item in order.items)


def find_existing_order_item(order_items, item_name, modifications=None):
    mods = modifications or ""

    for order_item in order_items:
        item_mods = order_item.modifications or ""
        if order_item.item_name.lower() == item_name.lower() and item_mods == mods:
            return order_item

    return None


def find_cart_item(order_items, item_name):
    exact_match = find_existing_order_item(order_items, item_name)

    if exact_match:
        return exact_match

    partial_matches = [
        item
        for item in order_items
        if item_name.lower() in item.item_name.lower()
    ]

    if len(partial_matches) == 1:
        return partial_matches[0]

    return None


def resolve_cart_item_name(item_name, menu, order_items):
    menu_item = find_menu_item(item_name, menu)

    if menu_item:
        cart_item = find_cart_item(order_items, menu_item["name"])
        if cart_item:
            return cart_item

    return find_cart_item(order_items, item_name)


def sync_order_total(db, order):
    order.total_price = recalculate_order_total(order)
    db.commit()


def format_order_summary(order, header):
    lines = [header]

    for item in order.items:
        line_total = item.quantity * item.unit_price

        if item.modifications:
            lines.append(
                f"- {item.quantity}x {item.item_name} ({item.modifications}) — ${line_total:.2f}"
            )
        else:
            lines.append(f"- {item.quantity}x {item.item_name} — ${line_total:.2f}")

    lines.append(f"Total: ${order.total_price:.2f}")

    return "\n".join(lines)


ADD_ALL_PHRASES = (
    "every item",
    "all items",
    "entire menu",
    "whole menu",
    "everything on the menu",
    "add all",
    "add everything",
)


def wants_add_all_menu(message):
    lower = message.lower()
    return any(phrase in lower for phrase in ADD_ALL_PHRASES)


def wants_cancel_order(message):
    lower = message.lower()
    return any(phrase in lower for phrase in CANCEL_ORDER_PHRASES)


def wants_call_restaurant(message):
    lower = message.lower()
    return any(phrase in lower for phrase in CALL_RESTAURANT_PHRASES)


def resolve_fast_intent(message, restaurant_info):
    lower = message.lower().strip()
    categories = restaurant_info.get("categories", [])

    if wants_call_restaurant(message):
        return {"intent": "call_restaurant"}

    if wants_cancel_order(message):
        return {"intent": "cancel_order"}

    if wants_add_all_menu(message):
        return {"intent": "add_all_to_order"}

    if lower in GREETING_PHRASES:
        return {"intent": "greeting"}

    if lower in {"clear cart", "clear my cart", "empty cart", "start over", "empty my order"}:
        return {"intent": "clear_cart"}

    for phrase in HOURS_PHRASES:
        if lower == phrase or phrase in lower:
            return {"intent": "ask_hours"}

    for phrase in CHECKOUT_PHRASES:
        if lower == phrase or lower.startswith(f"{phrase} "):
            return {"intent": "checkout"}

    for phrase in CART_PHRASES:
        if phrase in lower:
            return {"intent": "view_cart"}

    for phrase in MENU_PHRASES + ORDER_START_PHRASES:
        if phrase in lower:
            return {"intent": "ask_menu"}

    if lower == "order":
        return {"intent": "ask_menu"}

    for category in categories:
        normalized = normalize_category(category, categories)
        category_aliases = {category, category.rstrip("s")}
        category_aliases.update(
            alias for alias, value in CATEGORY_ALIASES.items() if value == category
        )

        if lower in category_aliases:
            return {"intent": "ask_menu_category", "category": normalized}

        for prefix in ("show ", "see ", "show me "):
            if lower == f"{prefix}{category}" or lower == f"{prefix}{category.rstrip('s')}":
                return {"intent": "ask_menu_category", "category": normalized}

    return None


def handle_unknown(customer_phone, message, restaurant_info):
    lower = message.lower().strip()
    categories = restaurant_info.get("categories", [])

    order_hints = (
        "order",
        "food",
        "eat",
        "hungry",
        "menu",
        "get",
        "want",
        "like",
    )

    if any(hint in lower for hint in order_hints):
        return format_category_prompt(categories)

    db = SessionLocal()

    try:
        order = get_building_order(db, customer_phone)

        if order and order.items:
            cart_summary = view_cart(customer_phone)
            return (
                f"{cart_summary}\n\n"
                "Say checkout when you're ready, or browse the menu to keep adding items."
            )
    finally:
        db.close()

    return (
        "Sorry, I couldn't understand that. You can browse the menu, view your cart, "
        "add or remove items, clear your cart, say checkout when you're ready, "
        "cancel order within 5 minutes of placing an order, or say call restaurant "
        "to order by phone."
    )


def format_call_restaurant(restaurant_info):
    phone = restaurant_info.get("contact", {}).get("phone", "")
    restaurant_name = restaurant_info["restaurant_name"]

    if not phone:
        return "Please visit us in person — phone ordering isn't available right now."

    return (
        f"Prefer to order by phone? Call {restaurant_name} at {phone} "
        "and our team will help you out."
    )


def build_all_menu_items(menu):
    return [
        {"name": item["name"], "quantity": 1, "modifications": ""}
        for item in menu
        if item.get("available", True)
    ]


def add_all_menu_items(customer_phone, restaurant_info):
    parsed = {"items": build_all_menu_items(restaurant_info["menu"])}
    return add_items_to_order(
        customer_phone, parsed, restaurant_info, compact_summary=True
    )


def add_items_to_order(customer_phone, parsed, restaurant_info, compact_summary=False):
    menu = restaurant_info["menu"]
    parsed_items = parsed.get("items") or []

    if not parsed_items:
        return "I couldn't quite catch that — which item would you like to add?"

    db = SessionLocal()

    try:
        order = get_or_create_building_order(db, customer_phone)
        added_lines = []
        item_count = 0

        for parsed_item in parsed_items:
            item_name = parsed_item.get("name")
            quantity = parsed_item.get("quantity", 1)
            modifications = parsed_item.get("modifications", "")

            menu_item = find_menu_item(item_name, menu)

            if menu_item is None:
                return f"Sorry, I could not find '{item_name}' on the menu."

            if not menu_item.get("available", True):
                return f"Sorry, {menu_item['name']} is unavailable right now."

            unit_price = float(menu_item["price"])
            existing_item = find_existing_order_item(
                order.items, menu_item["name"], modifications
            )

            if existing_item:
                existing_item.quantity += quantity
            else:
                db.add(
                    OrderItem(
                        order_id=order.id,
                        item_name=menu_item["name"],
                        quantity=quantity,
                        unit_price=unit_price,
                        modifications=modifications or None,
                    )
                )

            line_total = unit_price * quantity

            if modifications:
                added_lines.append(
                    f"- {quantity}x {menu_item['name']} ({modifications}) — ${line_total:.2f}"
                )
            else:
                added_lines.append(
                    f"- {quantity}x {menu_item['name']} — ${line_total:.2f}"
                )

            item_count += 1

        db.commit()
        db.refresh(order)
        sync_order_total(db, order)

        lines = [f"Added to order #{order.id}:"]

        if compact_summary or item_count > 5:
            lines.append(f"- {item_count} items added")
        else:
            lines.extend(added_lines)

        lines.append(f"Running total: ${order.total_price:.2f}")
        lines.append("Keep browsing, or say checkout when you're ready.")

        return "\n".join(lines)

    finally:
        db.close()


def view_cart(customer_phone):
    db = SessionLocal()

    try:
        expire_stale_building_orders(db)
        order = get_building_order(db, customer_phone)

        if order is None or not order.items:
            return "Your cart is empty. Browse the menu and let me know what you'd like."

        summary = format_order_summary(order, f"Your cart (order #{order.id}):")
        summary += (
            "\n\nYou can change quantities, remove items, clear your cart, "
            "or say checkout when you're ready."
        )

        return summary

    finally:
        db.close()


def remove_from_cart(customer_phone, parsed, restaurant_info):
    menu = restaurant_info["menu"]
    parsed_items = parsed.get("items") or []

    if not parsed_items:
        return "Which item would you like to remove?"

    db = SessionLocal()

    try:
        expire_stale_building_orders(db)
        order = get_building_order(db, customer_phone)

        if order is None or not order.items:
            return "Your cart is already empty."

        removed_lines = []

        for parsed_item in parsed_items:
            item_name = parsed_item.get("name")
            remove_quantity = parsed_item.get("quantity")
            cart_item = resolve_cart_item_name(item_name, menu, order.items)

            if cart_item is None:
                return f"'{item_name}' isn't in your cart."

            if remove_quantity is None or remove_quantity >= cart_item.quantity:
                removed_lines.append(f"- {cart_item.quantity}x {cart_item.item_name}")
                db.delete(cart_item)
            else:
                cart_item.quantity -= remove_quantity
                removed_lines.append(
                    f"- {remove_quantity}x {cart_item.item_name} "
                    f"({cart_item.quantity} remaining)"
                )

        db.commit()
        db.refresh(order)
        sync_order_total(db, order)

        if not order.items:
            return "Removed from your cart:\n" + "\n".join(removed_lines) + "\n\nYour cart is now empty."

        lines = ["Removed from your cart:"]
        lines.extend(removed_lines)
        lines.append(f"Updated total: ${order.total_price:.2f}")

        return "\n".join(lines)

    finally:
        db.close()


def update_cart_quantity(customer_phone, parsed, restaurant_info):
    menu = restaurant_info["menu"]
    parsed_items = parsed.get("items") or []

    if not parsed_items:
        return "Which item would you like to update?"

    db = SessionLocal()

    try:
        expire_stale_building_orders(db)
        order = get_building_order(db, customer_phone)

        if order is None or not order.items:
            return "Your cart is empty."

        updated_lines = []

        for parsed_item in parsed_items:
            item_name = parsed_item.get("name")
            new_quantity = parsed_item.get("quantity")

            if new_quantity is None or new_quantity < 0:
                return f"How many '{item_name}' would you like?"

            cart_item = resolve_cart_item_name(item_name, menu, order.items)

            if cart_item is None:
                return f"'{item_name}' isn't in your cart."

            if new_quantity == 0:
                updated_lines.append(f"- Removed {cart_item.item_name}")
                db.delete(cart_item)
            else:
                old_quantity = cart_item.quantity
                cart_item.quantity = new_quantity
                updated_lines.append(
                    f"- {cart_item.item_name}: {old_quantity} → {new_quantity}"
                )

        db.commit()
        db.refresh(order)
        sync_order_total(db, order)

        if not order.items:
            return "Updated your cart:\n" + "\n".join(updated_lines) + "\n\nYour cart is now empty."

        lines = ["Updated your cart:"]
        lines.extend(updated_lines)
        lines.append(f"Updated total: ${order.total_price:.2f}")

        return "\n".join(lines)

    finally:
        db.close()


def clear_cart(customer_phone):
    db = SessionLocal()

    try:
        expire_stale_building_orders(db)
        order = get_building_order(db, customer_phone)

        if order is None or not order.items:
            return "Your cart is already empty."

        for item in list(order.items):
            db.delete(item)

        order.total_price = 0.0
        db.commit()

        return "Your cart has been cleared. Browse the menu whenever you're ready to start again."

    finally:
        db.close()


def get_latest_confirmed_order(db, customer_phone):
    return (
        db.query(Order)
        .filter(Order.customer_phone == customer_phone, Order.status == "confirmed")
        .order_by(Order.id.desc())
        .first()
    )


def get_order_confirmed_at(order):
    return order.confirmed_at or order.created_at


def cancel_order(customer_phone):
    db = SessionLocal()

    try:
        order = get_latest_confirmed_order(db, customer_phone)

        if order is None:
            return "You don't have a recent order to cancel."

        confirmed_at = get_order_confirmed_at(order)
        cancel_deadline = confirmed_at + timedelta(minutes=CANCEL_ORDER_WINDOW_MINUTES)

        if datetime.utcnow() > cancel_deadline:
            return (
                f"Sorry, orders can only be cancelled within "
                f"{CANCEL_ORDER_WINDOW_MINUTES} minutes of placing them."
            )

        order.status = "cancelled"
        db.commit()

        return f"Order #{order.id} has been cancelled."

    finally:
        db.close()


def checkout_order(customer_phone, restaurant_info):
    db = SessionLocal()

    try:
        expire_stale_building_orders(db)
        order = get_building_order(db, customer_phone)

        if order is None or not order.items:
            return "Your order is empty. Browse the menu and add some items first."

        if not order.customer_name:
            set_awaiting_name(customer_phone)
            return "Before we place your order, what's your name?"

        order.status = "confirmed"
        order.confirmed_at = datetime.utcnow()
        order.total_price = recalculate_order_total(order)
        db.commit()

        lines = format_order_summary(
            order, f"Order #{order.id} confirmed!"
        ).split("\n")
        lines.append(restaurant_info["policies"]["payment"])
        lines.append(restaurant_info["policies"]["pickup"])
        lines.append(
            f"You can cancel this order within {CANCEL_ORDER_WINDOW_MINUTES} minutes "
            "by saying cancel order."
        )

        return "\n".join(lines)

    finally:
        db.close()


def handle_customer_message(customer_phone, message):
    restaurant_info = load_restaurant_info()

    db = SessionLocal()

    try:
        expire_stale_building_orders(db)
        awaiting_name = is_awaiting_name(db, customer_phone)
    finally:
        db.close()

    fast_intent = resolve_fast_intent(message, restaurant_info)

    if fast_intent:
        parsed = fast_intent
    else:
        try:
            parsed = parse_customer_message(message, restaurant_info)
        except Exception:
            parsed = {"intent": "unknown"}

    intent = parsed.get("intent")
    menu = restaurant_info["menu"]
    categories = restaurant_info.get("categories", [])
    hours = restaurant_info.get("hours", {})

    if awaiting_name:
        continue_intents = {
            "ask_menu",
            "ask_menu_category",
            "ask_hours",
            "ask_dietary_options",
            "greeting",
            "add_to_order",
            "remove_from_cart",
            "update_quantity",
            "checkout",
            "view_cart",
            "clear_cart",
            "add_all_to_order",
            "cancel_order",
            "call_restaurant",
        }

        if intent in continue_intents:
            clear_awaiting_name(customer_phone)
        else:
            name = parsed.get("customer_name") or message
            clear_awaiting_name(customer_phone)
            return save_customer_name(customer_phone, name, restaurant_info)

    if intent == "greeting":
        return handle_greeting(customer_phone, restaurant_info)

    if intent == "provide_name":
        name = parsed.get("customer_name")

        if not name:
            set_awaiting_name(customer_phone)
            return "What's your name?"

        return save_customer_name(customer_phone, name, restaurant_info)

    if intent == "ask_menu":
        return format_category_prompt(categories)

    if intent == "ask_menu_category":
        category = normalize_category(parsed.get("category"), categories)

        if not category:
            return format_category_prompt(categories)

        return format_category_menu(category, menu)

    if intent == "ask_dietary_options":
        dietary_preference = parsed.get("dietary_preference")

        if not dietary_preference:
            return "What dietary preference are you looking for? For example: vegan, vegetarian, or gluten-free."

        return format_dietary_options(menu, dietary_preference)

    if intent == "ask_hours":
        return format_hours(hours)

    if intent == "add_to_order":
        return add_items_to_order(customer_phone, parsed, restaurant_info)

    if intent == "add_all_to_order":
        return add_all_menu_items(customer_phone, restaurant_info)

    if intent == "view_cart":
        return view_cart(customer_phone)

    if intent == "remove_from_cart":
        return remove_from_cart(customer_phone, parsed, restaurant_info)

    if intent == "update_quantity":
        return update_cart_quantity(customer_phone, parsed, restaurant_info)

    if intent == "clear_cart":
        return clear_cart(customer_phone)

    if intent == "checkout":
        return checkout_order(customer_phone, restaurant_info)

    if intent == "cancel_order":
        return cancel_order(customer_phone)

    if intent == "call_restaurant":
        return format_call_restaurant(restaurant_info)

    return handle_unknown(customer_phone, message, restaurant_info)
