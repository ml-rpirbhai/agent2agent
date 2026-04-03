"""Product Catalog A2A Server.

Exposes a product catalog lookup agent via the Agent2Agent (A2A) protocol.
Other agents (e.g. customer support) can discover this agent's capabilities
through its agent card and send queries over HTTP.

Usage:
    python product_catalog.py
    python product_catalog.py --host 0.0.0.0 --port 9001 --log-level DEBUG
"""

from __future__ import annotations

import logging

import uvicorn
from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.models.google_llm import Gemini
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL_NAME = "gemini-2.5-flash-lite"
PRODUCT_CATALOG_HOST = "localhost"
PRODUCT_CATALOG_PORT = 8001
LOGGING_LEVEL = 'INFO'

RETRY_OPTIONS = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

PRODUCT_CATALOG: dict[str, str] = {
    "iphone 15 pro": "iPhone 15 Pro, $999, Low Stock (8 units), 128GB, Titanium finish",
    "samsung galaxy s24": "Samsung Galaxy S24, $799, In Stock (31 units), 256GB, Phantom Black",
    "dell xps 15": 'Dell XPS 15, $1,299, In Stock (45 units), 15.6" display, 16GB RAM, 512GB SSD',
    "macbook pro 14": (
        'MacBook Pro 14", $1,999, In Stock (22 units), M3 Pro chip, 18GB RAM, 512GB SSD'
    ),
    "sony wh-1000xm5": (
        "Sony WH-1000XM5 Headphones, $399, In Stock (67 units), Noise-canceling, 30hr battery"
    ),
    "ipad air": 'iPad Air, $599, In Stock (28 units), 10.9" display, 64GB',
    "lg ultrawide 34": 'LG UltraWide 34" Monitor, $499, Out of Stock, Expected: Next week',
}

AGENT_INSTRUCTION = """\
You are a product catalog specialist from an external vendor.
When asked about products, use the get_product_info tool to fetch data from the catalog.
Provide clear, accurate product information including price, availability, and specs.
If asked about multiple products, look up each one.
Be professional and helpful.
"""

# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


def get_product_info(product_name: str) -> str:
    """Look up product information by name.

    Args:
        product_name: Name of the product (e.g. "iPhone 15 Pro", "MacBook Pro 14").

    Returns:
        A string with product details or a list of available products if not found.
    """
    key = product_name.lower().strip()
    if key in PRODUCT_CATALOG:
        return f"Product: {PRODUCT_CATALOG[key]}"
    available = ", ".join(name.title() for name in PRODUCT_CATALOG)
    return f"Sorry, I don't have information for {product_name}. Available products: {available}"


# ---------------------------------------------------------------------------
# Agent / App factories
# ---------------------------------------------------------------------------
product_catalog_agent = LlmAgent(model=Gemini(model=MODEL_NAME, retry_options=RETRY_OPTIONS),
                                 name="product_catalog_agent",
                                 description="External vendor's catalog agent that provides \
                                              product information and availability",
                                 instruction=AGENT_INSTRUCTION,
                                 tools=[get_product_info])

# Start product_catalog_agent app on localhost
product_catalog_agent_app = to_a2a(product_catalog_agent, port=PRODUCT_CATALOG_PORT)


def main() -> None:
    logging.basicConfig(level=LOGGING_LEVEL, format="%(asctime)s  %(levelname)-8s  %(message)s")

    logger.info(f"Starting Product Catalog A2A on localhost:{PRODUCT_CATALOG_PORT}")
    logger.info(f"Agent card will be at http://{PRODUCT_CATALOG_HOST}:{PRODUCT_CATALOG_PORT}{AGENT_CARD_WELL_KNOWN_PATH}")

    # Host product_catalog_agent app on localhost
    uvicorn.run(product_catalog_agent_app, port=PRODUCT_CATALOG_PORT)


if __name__ == "__main__":
    main()
