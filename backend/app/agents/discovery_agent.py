import json
import os
from pathlib import Path

from app.schemas.product_identity import ProductIdentity

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


def _unwrap(data: dict) -> dict:
    wrapper_keys = ["product_identification", "product_analysis", "product_info"]
    for key in wrapper_keys:
        inner = data.get(key)
        if isinstance(inner, dict):
            return {**data, **inner}
    return data


def _flatten(value: str | list | dict) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        parts = [v for v in value.values() if isinstance(v, str)]
        return ", ".join(parts) if parts else ""
    if isinstance(value, list):
        parts = [str(v) for v in value if isinstance(v, str)]
        return ", ".join(parts) if parts else ""
    return ""


def _normalize_llm_output(data: dict) -> dict:
    data = _unwrap(data)
    name = data.get("name") or data.get("product_name") or data.get("product") or ""
    cat_val = data.get("category", "")
    cat = _flatten(cat_val)
    sub = _flatten(data.get("subcategory", ""))
    if not sub:
        if isinstance(cat_val, dict):
            sub = _flatten(cat_val.get("tertiary", ""))
        if not sub:
            sub = _flatten(data.get("product_type", ""))
        if not sub:
            sub = _flatten(data.get("specific_type", ""))
    kw = (data.get("normalized_keywords")
          or data.get("keywords")
          or data.get("search_keywords")
          or data.get("tags")
          or [])
    niche = (data.get("detected_niche")
             or data.get("target_niche")
             or data.get("customer_niche")
             or data.get("niche"))
    if not cat:
        cat = "Unknown"
    if not sub:
        sub = "Unknown"
    return {
        "name": name,
        "category": cat,
        "subcategory": sub,
        "variants": data.get("variants", []),
        "normalized_keywords": kw if isinstance(kw, list) else [],
        "detected_niche": niche if isinstance(niche, str) else None,
        "image_refs": data.get("image_refs", []),
        "source_url": data.get("source_url"),
    }


def _finalize_identity(
    parsed: dict,
    input_type: str,
    value: str,
    scraped_data: dict | None = None,
) -> ProductIdentity:
    normalized = _normalize_llm_output(parsed)
    if not normalized["name"]:
        normalized["name"] = value if input_type == "text" else (
            scraped_data.get("title", "Unknown Product") if scraped_data else "Unknown Product"
        )
    return ProductIdentity(**normalized)


async def analyze_product(
    input_type: str,
    value: str,
    scraped_data: dict | None = None,
    *,
    _mock_response: dict | None = None,
) -> ProductIdentity:
    if _mock_response is not None:
        return _finalize_identity(_mock_response, input_type, value, scraped_data)

    from anthropic import AsyncAnthropic

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
    )

    content = response.content[0].text if response.content else ""

    json_start = content.find("{")
    json_end = content.rfind("}") + 1
    if json_start >= 0 and json_end > json_start:
        content = content[json_start:json_end]

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM returned invalid JSON: {e}\nRaw: {content[:500]}")

    return _finalize_identity(parsed, input_type, value, scraped_data)
