import json
import logging
import os
from pathlib import Path

from anthropic import AsyncAnthropic

from app.schemas.product_identity import ProductIdentity
from app.schemas.validation_result import ValidationJudgment

logger = logging.getLogger("validation_agent")

PROMPT_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "prompts"
    / "validation"
    / "validation_agent_prompt.md"
)


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _build_identity_text(product: ProductIdentity) -> str:
    parts = [
        f"name: {product.name}",
        f"category: {product.category}",
        f"subcategory: {product.subcategory}",
    ]
    if product.normalized_keywords:
        parts.append(f"keywords: {', '.join(product.normalized_keywords)}")
    if product.detected_niche:
        parts.append(f"niche: {product.detected_niche}")
    if product.source_url:
        parts.append(f"source URL: {product.source_url}")
    return "\n".join(parts)


_STRICT_JUDGMENT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "is_flagged": {"type": "boolean"},
        "flags": {"type": "array", "items": {"type": "string"}},
        "reasoning": {"type": "string"},
    },
    "required": ["is_flagged", "flags", "reasoning"],
    "additionalProperties": False,
}


def _make_strict(obj: object) -> None:
    if isinstance(obj, dict):
        if obj.get("type") == "object":
            obj["additionalProperties"] = False
        for v in obj.values():
            _make_strict(v)
    elif isinstance(obj, list):
        for item in obj:
            _make_strict(item)


_make_strict(_STRICT_JUDGMENT_SCHEMA)


async def run_validation_judgment(
    product: ProductIdentity,
    *,
    _mock_response: dict | None = None,
) -> ValidationJudgment:
    if _mock_response is not None:
        return ValidationJudgment(**_mock_response)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    prompt = _load_prompt()
    identity_text = _build_identity_text(product)
    full_prompt = prompt.replace("{product_identity}", identity_text)

    client = AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system="You are a platform-policy compliance analyst. Return only valid JSON.",
        messages=[{"role": "user", "content": full_prompt}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": _STRICT_JUDGMENT_SCHEMA,
            }
        },
    )

    content = response.content[0].text if response.content else ""
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Structured output returned invalid JSON: {e}\nRaw: {content[:500]}")

    return ValidationJudgment(**parsed)
