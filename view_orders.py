from database import SessionLocal
from models import Order


db = SessionLocal()

orders = db.query(Order).all()

for order in orders:
    print(f"\nOrder #{order.id}")
    print(f"Name: {order.customer_name or '—'}")
    print(f"Phone: {order.customer_phone}")
    print(f"Status: {order.status}")
    print(f"Total: ${order.total_price:.2f}")
    print("Items:")

    for item in order.items:
        print(f"- {item.quantity}x {item.item_name} @ ${item.unit_price:.2f}")

db.close()