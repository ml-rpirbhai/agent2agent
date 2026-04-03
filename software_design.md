# A2A Agent Modules: Software Design

## 1. Overview

This project implements a two-agent system using Google's
[Agent Development Kit (ADK)](https://google.github.io/adk-docs/) and the
[Agent2Agent (A2A) Protocol](https://a2a-protocol.org/). A **Product Catalog
Agent** runs as a standalone A2A server, and a **Customer Support Agent** runs
as an interactive CLI chatbot that consumes the catalog agent over the network.

The architecture mirrors a real-world scenario where an external vendor exposes
product data via A2A while an internal support team integrates it transparently.

### Source

Adapted from the
[Kaggle Day 5a — Agent2Agent Communication](https://www.kaggle.com/code/kaggle5daysofai/day-5a-agent2agent-communication)
notebook (Google 5-Day AI Agents course).

---

## 2. Architecture

```
┌─────────────────────────────┐            ┌─────────────────────────────┐
│  customer_support.py        │            │  product_catalog.py         │
│                             │            │                             │
│  ┌───────────────────────┐  │   A2A      │  ┌───────────────────────┐  │
│  │ Customer Support      │──┼───HTTP────▶│  │ Product Catalog       │  │
│  │ LlmAgent              │  │  protocol  │  │ LlmAgent              │  │
│  │                       │  │            │  │                       │  │
│  │  sub_agents:          │  │            │  │  tools:               │  │
│  │   └ RemoteA2aAgent ───┼──┘            │  │   └ get_product_info  │  │
│  └───────────────────────┘  │            │  └───────────────────────┘  │
│                             │            │                             │
│  Runner                     │            │  to_a2a() → ASGI app       │
│  InMemorySessionService     │            │  uvicorn server            │
│  Interactive CLI loop       │            │  localhost:8001             │
└─────────────────────────────┘            └─────────────────────────────┘
         ▲                                           ▲
         │ stdin/stdout                              │ Agent Card served at
         │                                           │ /.well-known/agent-card.json
       User                                        Network
```

### Data Flow

1. User types a product question in the CLI.
2. `customer_support.py` wraps the input as `types.Content` and passes it to
   the `Runner`.
3. The Customer Support `LlmAgent` decides it needs product information and
   delegates to the `RemoteA2aAgent` sub-agent.
4. `RemoteA2aAgent` sends an HTTP POST (A2A JSON-RPC) to the Product Catalog
   server at `http://localhost:8001`.
5. The Product Catalog `LlmAgent` receives the request, calls
   `get_product_info()`, and returns the result.
6. The response flows back through A2A → `RemoteA2aAgent` → Customer Support
   Agent → CLI output.

---

## 3. Module Descriptions

### 3.1 `product_catalog.py` — A2A Server

| Item | Detail |
|---|---|
| **Purpose** | Expose a product catalog lookup agent via the A2A protocol. |
| **Entry point** | `main()` → `uvicorn.run()` |
| **Default address** | `localhost:8001` |
| **CLI args** | `--host`, `--port`, `--log-level` |

**Key symbols:**

- `PRODUCT_CATALOG: dict[str, str]` — mock product database (7 entries).
- `get_product_info(product_name: str) -> str` — tool function; performs
  case-insensitive lookup in `PRODUCT_CATALOG`.
- `create_agent() -> LlmAgent` — factory that builds the agent with model,
  instruction, and tool.
- `create_app(agent: LlmAgent, port: int) -> Starlette` — wraps the agent with
  `to_a2a()`.
- `main()` — parses args, configures logging, starts uvicorn.

### 3.2 `customer_support.py` — Interactive CLI Chatbot

| Item | Detail |
|---|---|
| **Purpose** | Provide a conversational interface to customers, delegating product queries to the remote catalog agent. |
| **Entry point** | `main()` → `asyncio.run(chat_loop(...))` |
| **CLI args** | `--catalog-url`, `--log-level` |

**Key symbols:**

- `check_catalog_server(url: str) -> bool` — pre-flight HTTP check against the
  agent card endpoint.
- `create_remote_agent(catalog_url: str) -> RemoteA2aAgent` — factory building
  the A2A client proxy.
- `create_support_agent(remote: RemoteA2aAgent) -> LlmAgent` — factory building
  the support agent with the remote sub-agent.
- `async chat_loop(runner: Runner, user_id: str, session_id: str) -> None` —
  REPL: reads stdin, sends to runner, prints final response.
- `main()` — parses args, validates connectivity, creates session, enters async
  chat loop.

---

## 4. Shared Configuration

| Setting | Value | Source |
|---|---|---|
| Gemini model | `gemini-2.5-flash-lite` | Hard-coded constant |
| Retry attempts | 5 | `types.HttpRetryOptions` |
| Retry backoff base | 7 | `types.HttpRetryOptions` |
| Retryable HTTP codes | 429, 500, 503, 504 | `types.HttpRetryOptions` |
| API key | `GOOGLE_API_KEY` | `.env` file / environment variable |

---

## 5. Project Files

```
a2a/
├── product_catalog.py      # A2A server (run first)
├── customer_support.py     # CLI chatbot  (run second)
├── pyproject.toml          # PEP 621 metadata, deps, ruff config
├── .env.example            # API key template
└── software_design.md      # This document
```

---

## 6. Prerequisites

- Python 3.11+
- A [Google Gemini API key](https://aistudio.google.com/app/api-keys)

---

## 7. How to Run

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install the project and its dependencies
pip install .

# 3. Configure the API key
cp .env .env
# Edit .env and paste your GOOGLE_API_KEY

# 4. Start the Product Catalog server (Terminal 1)
python product_catalog.py
# Server listening on http://localhost:8001

# 5. Start the Customer Support chatbot (Terminal 2)
python customer_support.py
# Interactive prompt appears — type product questions

# 6. Exit
# Type 'quit' or press Ctrl+C in Terminal 2
# Press Ctrl+C in Terminal 1 to stop the server
```

### Optional CLI flags

```bash
# Product Catalog
python product_catalog.py --host 0.0.0.0 --port 9001 --log-level DEBUG

# Customer Support
python customer_support.py --catalog-url http://myhost:9001 --log-level DEBUG
```

---

## 8. References

- [A2A Protocol Specification](https://a2a-protocol.org/latest/specification/)
- [ADK — Exposing Agents via A2A](https://google.github.io/adk-docs/a2a/quickstart-exposing/)
- [ADK — Consuming Remote Agents](https://google.github.io/adk-docs/a2a/quickstart-consuming/)
- [Kaggle Day 5a Notebook](https://www.kaggle.com/code/kaggle5daysofai/day-5a-agent2agent-communication)
