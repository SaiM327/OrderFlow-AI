import json
from datetime import datetime, timedelta

from database import SessionLocal
from models import Order, OrderItem

RESTAURANT_INFO_PATH = "restaurant_info.json"

KITCHEN_STATUSES = ("confirmed", "preparing", "ready", "completed")
ORDER_STATUS_LABELS = {
    "building": "In Cart",
    "confirmed": "New",
    "preparing": "Preparing",
    "ready": "Ready",
    "completed": "Completed",
    "cancelled": "Cancelled",
    "abandoned": "Abandoned",
}


def load_restaurant_info():
    with open(RESTAURANT_INFO_PATH, "r") as f:
        return json.load(f)


def save_restaurant_info(info):
    with open(RESTAURANT_INFO_PATH, "w") as f:
        json.dump(info, f, indent=2)
        f.write("\n")


def serialize_order_item(item):
    return {
        "id": item.id,
        "item_name": item.item_name,
        "quantity": item.quantity,
        "unit_price": item.unit_price,
        "modifications": item.modifications,
        "line_total": round(item.quantity * item.unit_price, 2),
    }


def serialize_order(order):
    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "status": order.status,
        "status_label": ORDER_STATUS_LABELS.get(order.status, order.status.title()),
        "total_price": round(order.total_price, 2),
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "confirmed_at": order.confirmed_at.isoformat() if order.confirmed_at else None,
        "items": [serialize_order_item(item) for item in order.items],
        "item_count": sum(item.quantity for item in order.items),
    }


def get_dashboard_stats():
    db = SessionLocal()

    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        active_orders = (
            db.query(Order)
            .filter(Order.status.in_(["confirmed", "preparing", "ready"]))
            .count()
        )

        candidate_orders = (
            db.query(Order)
            .filter(Order.status.in_(["confirmed", "preparing", "ready", "completed"]))
            .all()
        )

        today_orders = [
            order
            for order in candidate_orders
            if (order.confirmed_at or order.created_at) >= today_start
        ]

        today_revenue = sum(order.total_price for order in today_orders)

        info = load_restaurant_info()
        unavailable_count = sum(
            1 for item in info["menu"] if not item.get("available", True)
        )

        return {
            "restaurant_name": info["restaurant_name"],
            "active_orders": active_orders,
            "today_order_count": len(today_orders),
            "today_revenue": round(today_revenue, 2),
            "unavailable_items": unavailable_count,
        }
    finally:
        db.close()


def list_orders(status=None):
    db = SessionLocal()

    try:
        query = db.query(Order).order_by(Order.id.desc())

        if status:
            query = query.filter(Order.status == status)
        else:
            query = query.filter(
                Order.status.in_(
                    ["building", "confirmed", "preparing", "ready", "completed", "cancelled"]
                )
            )

        orders = query.limit(100).all()
        return [serialize_order(order) for order in orders]
    finally:
        db.close()


def update_order_status(order_id, status):
    if status not in KITCHEN_STATUSES + ("cancelled",):
        raise ValueError(f"Invalid status: {status}")

    db = SessionLocal()

    try:
        order = db.query(Order).filter(Order.id == order_id).first()

        if order is None:
            raise LookupError("Order not found")

        order.status = status
        db.commit()
        db.refresh(order)

        return serialize_order(order)
    finally:
        db.close()


def get_menu_items():
    info = load_restaurant_info()

    items = []
    for index, item in enumerate(info["menu"]):
        items.append(
            {
                "index": index,
                "name": item["name"],
                "price": item["price"],
                "category": item.get("category", ""),
                "tags": item.get("tags", []),
                "available": item.get("available", True),
            }
        )

    return {
        "categories": info.get("categories", []),
        "items": items,
    }


def set_menu_item_availability(item_name, available):
    info = load_restaurant_info()

    for item in info["menu"]:
        if item["name"].lower() == item_name.lower():
            item["available"] = available
            save_restaurant_info(info)
            return {
                "name": item["name"],
                "available": item["available"],
            }

    raise LookupError("Menu item not found")


def add_menu_item(name, price, category, tags=None, available=True):
    info = load_restaurant_info()
    categories = info.get("categories", [])

    name = name.strip()
    category = category.strip().lower()

    if not name:
        raise ValueError("Item name is required")

    if category not in categories:
        raise ValueError(f"Invalid category. Choose one of: {', '.join(categories)}")

    if price <= 0:
        raise ValueError("Price must be greater than 0")

    if any(item["name"].lower() == name.lower() for item in info["menu"]):
        raise ValueError("An item with this name already exists")

    new_item = {
        "name": name,
        "price": round(float(price), 2),
        "category": category,
        "tags": tags or [],
        "available": available,
    }

    info["menu"].append(new_item)
    save_restaurant_info(info)

    return {
        "name": new_item["name"],
        "price": new_item["price"],
        "category": new_item["category"],
        "tags": new_item["tags"],
        "available": new_item["available"],
    }
