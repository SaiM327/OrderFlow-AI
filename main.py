from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse

from bot import handle_customer_message

app = FastAPI()


@app.get("/")
def home():
    return {"status": "Restaurant bot is running"}


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...)
):
    print("Incoming WhatsApp message")
    print("From:", From)
    print("Body:", Body)

    customer_phone = From.replace("whatsapp:", "")
    customer_message = Body

    bot_response = handle_customer_message(
        customer_phone=customer_phone,
        message=customer_message
    )

    print("Bot response:", bot_response)

    twilio_response = MessagingResponse()
    twilio_response.message(bot_response)

    return Response(
        content=str(twilio_response),
        media_type="application/xml"
    )