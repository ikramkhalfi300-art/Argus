import json
import logging
import os
from pathlib import Path

from anthropic import AsyncAnthropic

from app.schemas.product_identity import ProductIdentity
from integrations.vision_model_client import download_image

logger = logging.getLogger("discovery_agent")

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent.parent / "prompts" / "discovery" / "discovery_agent_prompt.md"


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _build_input_text(input_type: str, value: str, scraped_data: dict | None = None) -> str:
    if input_type == "text":
        return f"product name: {value}"
    parts = [f"product URL: {value}"]
    if scraped_data:
        if scraped_data.get("title"):
            parts.append(f"page title: {scraped_data['title']}")
        if scraped_data.get("description"):
            parts.append(f"description: {scraped_data['description']}")
        if scraped_data.get("price"):
            parts.append(f"price: {scraped_data['price']}")
        if scraped_data.get("variants"):
            parts.append(f"variants: {', '.join(scraped_data['variants'])}")
        if scraped_data.get("images"):
            parts.append(f"image count: {len(scraped_data['images'])}")
    return "\n".join(parts)


def _make_strict_schema(schema: dict) -> dict:
    _add_no_extra(schema)
    return schema


def _add_no_extra(obj: object) -> None:
    if isinstance(obj, dict):
        if obj.get("type") == "object":
            obj["additionalProperties"] = False
        for v in obj.values():
            _add_no_extra(v)
    elif isinstance(obj, list):
        for item in obj:
            _add_no_extra(item)


_PRODUCT_SCHEMA = _make_strict_schema(ProductIdentity.model_json_schema())


def _make_niche_shortlist_schema() -> dict:
    item_schema = ProductIdentity.model_json_schema()
    schema: dict = {
        "type": "object",
        "properties": {
            "candidates": {
                "type": "array",
                "items": item_schema,
            }
        },
        "required": ["candidates"],
        "additionalProperties": False,
    }
    _make_strict_schema(schema)
    return schema


_NICHE_SHORTLIST_SCHEMA = _make_niche_shortlist_schema()


def _finalize_identity(
    data: dict,
    input_type: str,
    value: str,
    scraped_data: dict | None = None,
) -> ProductIdentity:
    if not data.get("name"):
        data["name"] = value if input_type == "text" else (
            scraped_data.get("title", "Unknown Product") if scraped_data else "Unknown Product"
        )
    return ProductIdentity(**data)


async def analyze_product(
    input_type: str,
    value: str,
    scraped_data: dict | None = None,
    *,
    _mock_response: dict | None = None,
) -> ProductIdentity:
    if _mock_response is not None:
        return _finalize_identity(_mock_response, input_type, value, scraped_data)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    prompt = _load_prompt()
    input_text = _build_input_text(input_type, value, scraped_data)
    full_prompt = prompt.replace("{input}", input_text)

    client = AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system="You are a product identification analyst. Return only valid JSON.",
        messages=[{"role": "user", "content": full_prompt}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": _PRODUCT_SCHEMA,
            }
        },
    )

    content = response.content[0].text if response.content else ""

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Structured output returned invalid JSON: {e}\nRaw: {content[:500]}")

    red_flags = parsed.get("authenticity_assessment") or parsed.get("red_flags")
    if red_flags:
        logger.info("Authenticity assessment: %s", json.dumps(red_flags, ensure_ascii=False))

    return _finalize_identity(parsed, input_type, value, scraped_data)


_IMAGE_SYSTEM_PROMPT = (
    "You are a product identification analyst. "
    "Identify the product shown in this image:\n"
    "1. The precise product category and subcategory\n"
    "2. 5-10 normalized search keywords a buyer would use\n"
    "3. The likely target customer niche\n"
    "4. Red flags if this looks like a knockoff/IP-infringing item\n"
    "Return structured JSON only. Do not guess brand names you cannot verify."
)


async def analyze_product_image(
    image_url: str,
    *,
    _mock_response: dict | None = None,
) -> ProductIdentity:
    if _mock_response is not None:
        return _finalize_identity(_mock_response, "image", image_url)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    media_type, b64_data = await download_image(image_url)

    client = AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=_IMAGE_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "What product is shown here? Identify its name, "
                            "category, subcategory, keywords, and target niche."
                        ),
                    },
                ],
            }
        ],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": _PRODUCT_SCHEMA,
            }
        },
    )

    content = response.content[0].text if response.content else ""

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Structured output returned invalid JSON: {e}\nRaw: {content[:500]}")

    red_flags = parsed.get("authenticity_assessment") or parsed.get("red_flags")
    if red_flags:
        logger.info("Authenticity assessment: %s", json.dumps(red_flags, ensure_ascii=False))

    return _finalize_identity(parsed, "image", image_url)


async def analyze_niche_shortlist(
    niche_query: str,
    *,
    _mock_response: list[dict] | None = None,
) -> list[ProductIdentity]:
    if _mock_response is not None:
        return [ProductIdentity(**item) for item in _mock_response]

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    prompt = _load_prompt()
    niche_section = prompt.split("--- NICHE SHORTLIST ---")[1].strip()
    full_prompt = niche_section.replace("{input}", niche_query)

    client = AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system="You are a product sourcing analyst. Return only valid JSON.",
        messages=[{"role": "user", "content": full_prompt}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": _NICHE_SHORTLIST_SCHEMA,
            }
        },
    )

    content = response.content[0].text if response.content else ""

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Structured output returned invalid JSON: {e}\nRaw: {content[:500]}")

    candidates = parsed.get("candidates", [])
    results: list[ProductIdentity] = []
    for item in candidates:
        if not item.get("name"):
            item["name"] = "Unknown Niche Product"
        results.append(ProductIdentity(**item))

    if not results:
        raise RuntimeError("Niche shortlist returned zero candidates")

    return results
