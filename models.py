from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Order(Base): #table for orders
    __tablename__ = "orders"

    #only actually creates the orders
    id = Column(Integer, primary_key=True, index=True)
    customer_phone = Column(String, index=True)
    customer_name = Column(String, nullable=True)

    status = Column(String, default="confirmed")
    total_price = Column(Float, default=0.0)
    special_notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)

    items = relationship("OrderItem", back_populates="order") #double ended link between orders and order items, so you can easily access the order from an order item and vice versa


class OrderItem(Base): #table for a single order item, which is linked to the orders table via order_id
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(Integer, ForeignKey("orders.id"))
    item_name = Column(String)
    quantity = Column(Integer)
    unit_price = Column(Float)
    modifications = Column(String, nullable=True)

    order = relationship("Order", back_populates="items") #double-ended link between orders and order items, so you can easily access the order from an order item and vice versa