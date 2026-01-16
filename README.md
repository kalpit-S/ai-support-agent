# AI Support Agent

A multi-channel AI customer support agent for an e-commerce store (Macrocenter, a PC parts retailer), demonstrating production patterns: **LLM tool calling**, **Redis message batching**, **real-time voice**, and **cross-channel context** (Email, SMS, Voice).

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![React](https://img.shields.io/badge/React-18-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Redis](https://img.shields.io/badge/Redis-7-red)

## What This Demonstrates

| Capability | Implementation |
|------------|----------------|
| **Cross-Channel Context** | Same customer recognized across Email, SMS, and Voice - agent references prior conversations |
| **LLM Tool Calling** | 8 structured tools with function calling (Claude Sonnet 4.5 for text, Gemini 2.5 Flash for voice) |
| **Real-Time Voice** | Deepgram Voice Agent API (STT → LLM → TTS in one WebSocket) |
| **Channel Selection** | Agent can choose to respond via a different channel (e.g., email details after SMS request) |
| **Message Batching** | Redis-based batching groups rapid messages before LLM processing |
| **Modern Frontend** | React + Vite + Tailwind with native-looking channel UIs (Gmail, iMessage, Phone) |
| **Structured Extraction** | Customer info extracted into typed database fields (issue type, severity, order number) |
| **Human-in-the-Loop** | Auto-escalation for high-value refunds (>$500), fraud, complex disputes |

---

## Demo Flow

The key demo shows **cross-channel context** - the agent remembers you across different communication channels:

1. **Email Tab** (Gmail-style UI) → "What's the status of order ORD-1001?"
   - Agent looks up order, responds with formatted details
   - Response appears in inbox thread with markdown rendering

2. **SMS Tab** (iMessage-style UI) → "Can I get a refund on that RTX 4090?"
   - Agent references the email conversation: "I see you asked about ORD-1001 earlier..."
   - Extracts customer info (issue type: refund, order: ORD-1001)

3. **Voice Tab** (Phone call UI) → Start a voice call
   - Greeting acknowledges prior conversation: "I can see we've been chatting over email or text..."
   - Agent can use `send_followup` tool to email/text details during the call

The **Unified Context** sidebar shows all interactions in a single timeline with tool execution timing.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React + Vite)                            │
│  ┌─────────────────────────────────────────┬─────────────────────────────┐  │
│  │         Channel Views (Tabs)            │     Unified Context         │  │
│  │  ┌─────────┬─────────┬─────────┐        │  ┌───────────────────────┐  │  │
│  │  │  Email  │   SMS   │  Voice  │        │  │ Customer Info         │  │  │
│  │  │ (Gmail) │(iMessage)│ (Phone) │        │  │ Conversation Timeline │  │  │
│  │  └─────────┴─────────┴─────────┘        │  │ Tool Executions       │  │  │
│  └─────────────────────────────────────────┴─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                                    │
         (Email/SMS via REST)                   (Voice via WebSocket)
                    │                                    │
                    ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API (FastAPI)                                   │
│  • POST /webhook/sms, /webhook/email                                        │
│  • WebSocket /ws/voice → Deepgram Voice Agent                               │
│  • Customer lookup with cross-channel linking                               │
└─────────────────────┬───────────────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌───────────────────────┐   ┌───────────────────────────────────────────────┐
│   Redis Batcher       │   │            Deepgram Voice Agent                │
│  • 5s message window  │   │  • Flux STT → Gemini 2.5 Flash → Aura-2 TTS   │
│  • Groups rapid msgs  │   │  • Same tools as text channels + send_followup│
└───────────┬───────────┘   │  • Receives prior email/SMS conversation      │
            │               └───────────────────────────────────────────────┘
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WORKER                                          │
│  • Claude Sonnet 4.5 via OpenRouter                                         │
│  • Tool calling loop (max 5 iterations)                                     │
│  • Channel selection ([EMAIL] or [SMS] prefix in response)                  │
│  • Saves responses + extracted customer data                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Tools

### Text Channels (Email/SMS)

| Tool | Description | Example Use |
|------|-------------|-------------|
| `lookup_order` | Get order details, status, tracking | "Where's my order ORD-1001?" |
| `check_inventory` | Check stock levels by SKU or name | "Do you have RTX 4090 in stock?" |
| `process_refund` | Issue full/partial refunds (>$500 auto-escalates) | "I need a refund for this DOA GPU" |
| `update_order_status` | Update status, add tracking | "Mark order as shipped" |
| `create_return_label` | Generate return shipping label | "I need to return this motherboard" |
| `search_knowledge_base` | Find help articles | "What's your return policy?" |
| `save_customer_info` | Extract customer details | Saves name, issue type, severity, order number |
| `escalate_to_human` | Create support ticket | Fraud, large refunds, disputes |

### Voice Channel (Additional)

| Tool | Description | Example Use |
|------|-------------|-------------|
| `send_followup` | Send email/SMS during voice call | "I'll email you that return label right now" |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenRouter API key (for text channels)
- Deepgram API key (for voice - optional)

### Setup

```bash
# Clone and configure
cp .env.example .env
# Edit .env with your API keys:
# - OPENROUTER_API_KEY (required)
# - DEEPGRAM_API_KEY (optional, for voice)

# Start all services
docker-compose up -d

# Open the UI
open http://localhost:3000
```

### Verify Setup

```bash
# Check all containers are healthy
docker-compose ps

# View worker logs to see LLM tool calls
docker-compose logs -f worker

# View API logs for voice/webhook activity
docker-compose logs -f api
```

---

## Database Schema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              7 TABLES                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐   │
│  │   customers     │       │    messages     │       │    tickets      │   │
│  ├─────────────────┤       ├─────────────────┤       ├─────────────────┤   │
│  │ id              │◄──────│ customer_id     │       │ customer_id     │──►│
│  │ phone_number    │       │ direction       │       │ article_id      │──►│
│  │ email           │       │ channel         │       │ status          │   │
│  │ first_name      │       │ content         │       │ issue_type      │   │
│  │ extracted_data  │       │ batch_id        │       │ severity        │   │
│  └─────────────────┘       └─────────────────┘       └─────────────────┘   │
│                                                              │              │
│  ┌─────────────────┐       ┌─────────────────┐              │              │
│  │ knowledge_base  │◄──────────────────────────────────────-┘              │
│  ├─────────────────┤                                                       │
│  │ article_id      │                                                       │
│  │ title           │                                                       │
│  │ content         │                                                       │
│  │ metadata (JSONB)│                                                       │
│  └─────────────────┘                                                       │
│                                                                             │
│  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐   │
│  │    products     │       │   inventory     │       │     orders      │   │
│  ├─────────────────┤       ├─────────────────┤       ├─────────────────┤   │
│  │ sku             │◄──────│ product_id      │       │ order_number    │   │
│  │ name            │       │ quantity        │       │ customer_id     │──►│
│  │ price           │       │ warehouse       │       │ status          │   │
│  │ category        │       │ low_stock_thresh│       │ total           │   │
│  └────────┬────────┘       └─────────────────┘       │ tracking_number │   │
│           │                                          └────────┬────────┘   │
│           │         ┌─────────────────┐                       │            │
│           │         │  order_items    │                       │            │
│           │         ├─────────────────┤                       │            │
│           └────────►│ product_id      │◄──────────────────────┘            │
│                     │ order_id        │                                    │
│                     │ sku, quantity   │                                    │
│                     │ unit_price      │                                    │
│                     └─────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `customers` | Customer records linked across channels | `phone_number`, `email`, `extracted_data` (JSONB) |
| `messages` | All conversation messages | `customer_id`, `direction`, `channel`, `batch_id` |
| `tickets` | Support tickets for escalation | `customer_id`, `status`, `severity` |
| `knowledge_base` | Help articles the agent can search | `article_id`, `title`, `content`, `metadata` (JSONB) |
| `products` | Product catalog | `sku`, `name`, `price`, `category` |
| `inventory` | Stock levels per product | `product_id`, `quantity`, `low_stock_threshold` |
| `orders` | Customer orders | `order_number`, `status`, `total`, `tracking_number` |
| `order_items` | Line items in orders | `order_id`, `product_id`, `quantity`, `unit_price` |

---

## Sample Data

The database is seeded with test data for the demo:

| Entity | Examples |
|--------|----------|
| **Orders** | ORD-1001 (RTX 4090, delivered), ORD-1002 (Ryzen 9, shipped), ORD-1003 (750W PSU, pending) |
| **Products** | RTX 4090, RTX 4080, Ryzen 9 7950X, i9-14900K, DDR5 RAM, NVMe SSDs, PSUs |
| **Knowledge Base** | Return policy, GPU compatibility, PSU requirements, shipping info |

---

## Project Structure

```
.
├── frontend/                     # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/
│   │   │   ├── channels/         # EmailView, SmsView (native UIs)
│   │   │   ├── voice/            # VoiceView, Waveform
│   │   │   ├── context/          # UnifiedContext sidebar
│   │   │   └── layout/           # AppShell
│   │   ├── hooks/                # useChat, useVoice, usePolling
│   │   ├── stores/               # Zustand state management
│   │   └── api/                  # API client
│   └── Dockerfile
│
├── api/                          # FastAPI service
│   ├── routes/
│   │   ├── webhook.py            # SMS/Email webhooks
│   │   └── debug.py              # Customer/message endpoints
│   ├── voice/
│   │   ├── router.py             # WebSocket /ws/voice
│   │   ├── agent.py              # Deepgram Voice Agent client
│   │   └── tools.py              # Voice tool executor
│   └── main.py
│
├── worker/                       # Background message processor
│   ├── conversation/
│   │   ├── engine.py             # LLM orchestration
│   │   ├── tools.py              # 8 agent tools
│   │   └── prompts.py            # System prompts with policies
│   ├── llm/
│   │   └── openrouter_client.py  # Claude Sonnet 4.5 client
│   └── batcher.py                # Redis batch polling
│
├── db/
│   ├── init.sql                  # Schema (7 tables)
│   └── seed.sql                  # Sample orders, products, KB articles
│
├── tests/                        # pytest test suite
│
└── docker-compose.yml
```

---

## Key Technical Patterns

### 1. Cross-Channel Customer Linking

Customers are linked across channels by email/phone:

```python
# When SMS arrives, link to existing email customer
customer = db.query(Customer).filter(
    Customer.email == demo_email,
    Customer.phone_number.is_(None)
).first()
if customer:
    customer.phone_number = payload.from_number  # Link phone to email customer
```

### 2. Cross-Channel Context in Prompts

The agent receives full conversation history across channels:

```python
# Voice agent receives prior email/SMS conversation
PREVIOUS CONVERSATION WITH THIS CUSTOMER (from email/SMS):
Customer [EMAIL]: What's the status of order ORD-1001?
Agent [EMAIL]: Your order has been delivered...
Customer [SMS]: Can I get a refund?
```

### 3. Channel Selection

Agent can choose to respond via a different channel when appropriate:

```python
# Worker parses channel prefix from LLM response
if response_text.startswith("[EMAIL]"):
    outbound_channel = "email"
    response_text = response_text[7:].lstrip()
elif response_text.startswith("[SMS]"):
    outbound_channel = "sms"
    response_text = response_text[5:].lstrip()
```

### 4. Message Batching

Groups rapid messages before LLM processing:

```
Customer sends: "Hi" then "Order 1001" then "status?"
Without batching: 3 LLM calls ($$$)
With batching: 1 LLM call after 5s idle window
```

### 5. Voice Agent Pipeline

Single WebSocket to Deepgram handles STT → LLM → TTS:

```python
{
    "agent": {
        "listen": {"provider": {"type": "deepgram", "model": "flux-general-en"}},
        "think": {"provider": {"type": "google", "model": "gemini-2.5-flash"}},
        "speak": {"provider": {"type": "deepgram", "model": "aura-2-theia-en"}}
    }
}
```

### 6. Tool Calling Loop

Agent can chain multiple tools per turn (max 5 iterations):

```python
while response.tool_calls and iteration < max_iterations:
    for tool_call in response.tool_calls:
        result = executor.execute(tool_call.name, tool_call.arguments)
    response = client.chat(messages, tools=TOOL_DEFINITIONS)
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | required | LLM API key for text channels |
| `OPENROUTER_MODEL` | `anthropic/claude-sonnet-4.5` | Model for text (SMS/Email) |
| `DEEPGRAM_API_KEY` | optional | Required for voice channel |
| `BATCH_WINDOW_SECONDS` | `5` | Seconds to wait before processing batch |
| `POLL_INTERVAL_SECONDS` | `1` | How often worker checks for batches |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/webhook/sms` | POST | SMS webhook (Twilio format) |
| `/webhook/email` | POST | Email webhook (SendGrid format) |
| `/ws/voice` | WebSocket | Real-time voice via Deepgram |
| `/customers` | GET | List all customers |
| `/customers/{id}` | GET | Get customer with messages |

---

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test files
pytest tests/test_api.py -v
pytest tests/test_worker.py -v
pytest tests/test_tools.py -v

# With coverage
pytest tests/ --cov=api --cov=worker
```

---

## Security Notes

**This is a demonstration project.** For production:

- Validate Twilio/SendGrid webhook signatures
- Replace `allow_origins=["*"]` with specific domains
- Add authentication for customer data endpoints
- Sanitize PII from logs
- Add rate limiting
- Use environment-specific database credentials

---

## License

MIT
