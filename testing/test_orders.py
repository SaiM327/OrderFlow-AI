from database import SessionLocal
from models import Order, OrderItem

db = SessionLocal()

order = Order(
    customer_phone="+15551234567",
    customer_name="John Doe",
    status="confirmed",
    total_price=21.98,
)

db.add(order)
db.commit()
db.refresh(order)

item = OrderItem(
    order_id=order.id, item_name="Vegan Bowl", quantity=2, unit_price=10.99
)

db.add(item)
db.commit()

print(f"Created order #{order.id}")
