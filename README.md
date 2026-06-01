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

## Project Structure

```text
OrderFlowAI/
│
├── main.py                 # FastAPI webhook server
├── bot.py                  # Business logic layer
├── ai_parser.py            # LLM intent parsing
├── database.py            # Database configuration
├── models.py              # SQLAlchemy models
├── init_db.py             # Database initialization
├── restaurant_info.json   # Restaurant menu and hours
├── view_orders.py         # Database inspection utility
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
- Restaurant management dashboard
- Multi-restaurant support
- Voice ordering integration
- Instagram and SMS support

---

## Author

Sai Minnal

Built as a full-stack AI application demonstrating conversational AI, backend architecture, webhook integrations, and database-driven order management.
