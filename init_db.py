#when this file is run, an SQLite database named orders.db will be created in the same directory, and it will contain two tables: orders and order_items, with the appropriate columns and relationships defined in the models.py file.

from database import Base, engine
from models import Order, OrderItem

Base.metadata.create_all(bind=engine)

print("Database tables created successfully.")