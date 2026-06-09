import os

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")

from bot import handle_customer_message
from dashboard import (
    add_menu_item,
    get_dashboard_stats,
    get_menu_items,
    list_orders,
    set_menu_item_availability,
    update_order_status,
)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


class OrderStatusUpdate(BaseModel):
    status: str


class MenuAvailabilityUpdate(BaseModel):
    available: bool


class MenuItemCreate(BaseModel):
    name: str
    price: float
    category: str
    tags: list[str] = []
    available: bool = True


@app.get("/")
def home():
    return {"status": "Restaurant bot is running"}


@app.get("/dashboard")
def dashboard_page():
    return FileResponse("static/dashboard/index.html")


@app.get("/api/dashboard/stats")
def dashboard_stats():
    return get_dashboard_stats()


@app.get("/api/dashboard/orders")
def dashboard_orders(status: str | None = None):
    return list_orders(status=status)


@app.patch("/api/dashboard/orders/{order_id}")
def dashboard_update_order(order_id: int, payload: OrderStatusUpdate):
    try:
        return update_order_status(order_id, payload.status)
    except LookupError:
        raise HTTPException(status_code=404, detail="Order not found")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/api/dashboard/menu")
def dashboard_menu():
    return get_menu_items()


@app.post("/api/dashboard/menu")
def dashboard_create_menu_item(payload: MenuItemCreate):
    try:
        return add_menu_item(
            name=payload.name,
            price=payload.price,
            category=payload.category,
            tags=payload.tags,
            available=payload.available,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.patch("/api/dashboard/menu/{item_name}")
def dashboard_update_menu_item(item_name: str, payload: MenuAvailabilityUpdate):
    try:
        return set_menu_item_availability(item_name, payload.available)
    except LookupError:
        raise HTTPException(status_code=404, detail="Menu item not found")


def send_whatsapp_reply(to: str, body: str) -> bool:
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_WHATSAPP_FROM:
        return False

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(body=body, from_=TWILIO_WHATSAPP_FROM, to=to)
        print("WhatsApp reply sent via Twilio API")
        return True
    except Exception as error:
        print("Failed to send WhatsApp reply via Twilio API:", error)
        return False


def twiml_response(message: str | None = None) -> Response:
    twilio_response = MessagingResponse()

    if message:
        twilio_response.message(message)

    return Response(
        content=str(twilio_response),
        media_type="application/xml",
    )


@app.post("/webhook/whatsapp")
def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...)
):
    print("Incoming WhatsApp message")
    print("From:", From)
    print("Body:", Body)

    customer_phone = From.replace("whatsapp:", "")
    customer_message = Body

    try:
        bot_response = handle_customer_message(
            customer_phone=customer_phone,
            message=customer_message
        )
    except Exception as error:
        print("Error handling message:", error)
        bot_response = (
            "Sorry, something went wrong on our end. Please try again in a moment."
        )

    print("Bot response:", bot_response)

    if send_whatsapp_reply(From, bot_response):
        return twiml_response()

    print("Falling back to TwiML reply")
    return twiml_response(bot_response)
