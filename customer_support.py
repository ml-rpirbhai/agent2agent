"""Customer Support Interactive Chatbot.

Consumes a remote Product Catalog agent over the A2A protocol and exposes an
interactive CLI for customers to ask product questions.

Usage:
    python customer_support.py
    python customer_support.py --catalog-url http://myhost:9001 --log-level DEBUG
"""

from __future__ import annotations

import asyncio
import logging
import uuid

import requests
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL_NAME = "gemini-2.5-flash-lite"
PRODUCT_CATALOG_URL = "http://localhost:8001"
LOGGING_LEVEL = 'INFO'
APP_NAME = "customer_support_agent_app"

RETRY_OPTIONS = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

AGENT_INSTRUCTION = """\
You are a friendly and professional customer support agent.

When customers ask about products:
1. Use the product_catalog_agent sub-agent to look up product information.
2. Provide clear answers about pricing, availability, and specifications.
3. If a product is out of stock, mention the expected availability.
4. Be helpful and professional!

Always get product information from the product_catalog_agent before answering
customer questions.
"""

# ---------------------------------------------------------------------------
# Connectivity check
# ---------------------------------------------------------------------------
def check_product_catalog_server(base_url: str = PRODUCT_CATALOG_URL, timeout: int = 5):
    """Return True if the Product Catalog agent card can be retrieved"""
    card_url = f"{base_url}{AGENT_CARD_WELL_KNOWN_PATH}"
    try:
        resp = requests.get(card_url, timeout=timeout)
        if resp.status_code == 200:
            logger.info("Product Catalog agent card fetched from %s", card_url)
            return
        else:
            error = f"Agent card returned HTTP {resp.status_code}: {resp.text}"
            logger.error(error)
            raise ConnectionError(error)
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Product Catalog server at %s", base_url)
        raise
    except requests.exceptions.Timeout:
        logger.error("Timeout reaching Product Catalog server at %s", base_url)
        raise

# ---------------------------------------------------------------------------
# Agent factories
# ---------------------------------------------------------------------------
# Client-side proxy for the remote Product Catalog agent
remote_a2a_product_catalog_agent = RemoteA2aAgent(name="product_catalog_agent",
                                                  description=("Remote product catalog agent from external vendor \
                                                                that provides product information"),
                                                  agent_card=f"{PRODUCT_CATALOG_URL}{AGENT_CARD_WELL_KNOWN_PATH}")


# Customer Support agent with *remote_a2a_product_catalog_agent* as a sub-agent
customer_support_agent = LlmAgent(model=Gemini(model=MODEL_NAME, retry_options=RETRY_OPTIONS),
                                  name="customer_support_agent",
                                  description="A customer support assistant that helps customers with \
                                               product inquiries",
                                  instruction=AGENT_INSTRUCTION,
                                  sub_agents=[remote_a2a_product_catalog_agent])


# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------
async def chat_loop(runner: Runner, user_id: str, session_id: str) -> None:
    """Interactive REPL that reads user input and prints the agent's response."""
    print("\nCustomer Support Agent  (type 'quit' or 'exit' to leave)\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        content = types.Content(parts=[types.Part(text=user_input)])

        print("Agent: ", end="", flush=True)
        # Send user's message to Customer Support agent
        async for event in runner.run_async(user_id=user_id,
                                            session_id=session_id,
                                            new_message=content):
            # Print agent response
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text"):
                        print(part.text)
        print()


def main() -> None:
    logging.basicConfig(level=LOGGING_LEVEL, format="%(asctime)s  %(levelname)-8s  %(message)s")

    check_product_catalog_server()

    session_service = InMemorySessionService()
    user_id = "cli_user"
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    runner = Runner(agent=customer_support_agent, app_name=APP_NAME, session_service=session_service)

    async def _run() -> None:
        await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        await chat_loop(runner, user_id, session_id)

    asyncio.run(_run())


if __name__ == "__main__":
    main()
