# OrderFlow AI

An AI-powered restaurant ordering assistant that allows customers to interact with restaurants through WhatsApp using natural language.

Customers can:
- View menu items
- Ask about operating hours
- Request dietary recommendations (vegan, vegetarian, etc.)
- Place food orders through conversational messages

Orders are automatically parsed, validated, and stored in a relational database for restaurant staff to manage.

---

## Demo Workflow

Customer sends:

> Can I get 2 vegan bowls?

System flow:

```text
WhatsApp
    ↓
Twilio Webhook
    ↓
FastAPI
    ↓
Groq LLM
    ↓
Intent + Entity Extraction
    ↓
Business Logic Layer
    ↓
SQLite Database
    ↓
WhatsApp Response
```

Response:

```text
Got it — I created order #5:

- 2x Vegan Bowl — $21.98

Total: $21.98
Payment is handled in-store.
```

---

## Features

### Customer Features

- Natural-language ordering
- Menu inquiries
- Restaurant hours inquiries
- Dietary recommendations
- Order confirmations

### AI Features

- Intent classification
- Entity extraction
- Menu item normalization
- Structured JSON generation

### Backend Features

- Persistent order storage
- Relational database design
- Webhook-based architecture
- Modular service layers

---

## Architecture

```text
Customer
    ↓
WhatsApp
    ↓
Twilio
    ↓
FastAPI Webhook
    ↓
AI Parsing Layer (Groq LLM)
    ↓
Business Logic Layer
    ↓
Database Layer (SQLAlchemy + SQLite)
    ↓
Response Generation
    ↓
WhatsApp
```

---

## Tech Stack

### Backend

- Python
- FastAPI

### AI

- Groq API
- Llama 3.3 70B

### Database

- SQLite
- SQLAlchemy ORM

### Messaging

- Twilio WhatsApp Sandbox
- ngrok

---

## How to Run Locally

Everything runs from **one local Python server** (`uvicorn`). SQLite is a file on disk (no separate DB server). Groq and Twilio are cloud APIs — you just need API keys in `.env` and an internet connection.

### One-time setup

1. Create and activate the virtual environment (if you haven't already):

   ```bash
   cd OrderFlow-AI
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies (FastAPI, uvicorn, SQLAlchemy, Groq, Twilio, python-dotenv, etc.).

3. Create a `.env` file in the project root:

   ```env
   GROQ_API_KEY=your_groq_key
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ```

4. Initialize the database (first time only):

   ```bash
   python init_db.py
   ```

5. Join the [Twilio WhatsApp Sandbox](https://console.twilio.com/) from your phone and set the webhook URL to your public ngrok URL + `/webhook/whatsapp` (see below).

### Every time you want to use the app

**Terminal 1 — start the server (required):**

```bash
cd OrderFlow-AI
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

Verify it's running:

```bash
curl http://localhost:8000/
# → {"status":"Restaurant bot is running"}
```

**Terminal 2 — ngrok tunnel (WhatsApp only):**

Twilio can't reach `localhost`, so expose port 8000 to the internet:

```bash
ngrok http 8000
```

Copy the HTTPS URL ngrok gives you and set it in Twilio as:

```text
https://YOUR-NGROK-URL/webhook/whatsapp
```

If you use a reserved ngrok domain and see "endpoint is already online", the tunnel may still be running from a previous session. Confirm with:

```bash
curl https://YOUR-NGROK-URL/
```

### What to open

| Use case | What you need running | Where to go |
|----------|----------------------|-------------|
| Staff dashboard | Terminal 1 only | http://localhost:8000/dashboard |
| WhatsApp bot | Terminal 1 + ngrok | Message the Twilio sandbox number from your phone |
| Inspect orders in CLI | Terminal 1 not required | `python view_orders.py` (with venv active) |

### What you do NOT start separately

- **SQLite (`orders.db`)** — used automatically when the FastAPI app runs
- **Groq** — called over the internet when the AI parser is needed
- **Twilio** — cloud service; forwards WhatsApp messages to your webhook
- **Dashboard frontend** — static files served by the same FastAPI process

### Troubleshooting

- **Import errors / missing packages** — make sure you ran `source venv/bin/activate` before any Python command.
- **WhatsApp messages not arriving** — check that uvicorn and ngrok are both running and the Twilio webhook URL matches your current ngrok URL.
- **No reply on WhatsApp** — Twilio sandbox accounts have a daily message limit (50/day). Check server logs for Twilio API errors.

---

## Project Structure

```text
OrderFlowAI/
│
├── main.py                 # FastAPI webhook server + dashboard routes
├── bot.py                  # Business logic layer
├── ai_parser.py            # LLM intent parsing
├── dashboard.py            # Staff dashboard API logic
├── database.py             # Database configuration
├── models.py               # SQLAlchemy models
├── init_db.py              # Database initialization
├── restaurant_info.json    # Restaurant menu and hours
├── view_orders.py          # Database inspection utility
│
├── static/dashboard/       # Staff dashboard UI (HTML, CSS, JS)
│
├── testing/
│   ├── test_ai.py
│   ├── test_bot.py
│   └── test_groq.py
│
└── .gitignore
```

---

## Database Schema

### Orders

| Field | Type |
|---------|---------|
| id | Integer |
| customer_phone | String |
| status | String |
| total_price | Float |
| created_at | Timestamp |

### Order Items

| Field | Type |
|---------|---------|
| id | Integer |
| order_id | Foreign Key |
| item_name | String |
| quantity | Integer |
| unit_price | Float |
| modifications | String |

---

## Key Engineering Decisions

A major design goal was separating responsibilities into layers:

### AI Layer

Responsible only for understanding customer messages and generating structured JSON.

### Business Logic Layer

Responsible for validating menu items, processing orders, and generating responses.

### Database Layer

Responsible for persisting orders and order items.

### Messaging Layer

Responsible for receiving and sending WhatsApp messages through Twilio.

This separation made the system easier to test, debug, and extend.

---

## Future Work

- Reservation management
- Order status tracking
- Customer profiles
- Multi-restaurant support
- Voice ordering integration
- Instagram and SMS support

---

## Author

Sai Minnal

Built as a full-stack AI application demonstrating conversational AI, backend architecture, webhook integrations, and database-driven order management.
