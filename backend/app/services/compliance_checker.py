import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.schemas.product_identity import ProductIdentity


@dataclass
class BlocklistRule:
    title: str
    categories: list[str] = field(default_factory=list)
    subcategories: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    action: str = "block"


@dataclass
class ComplianceResult:
    flagged: bool
    matched_rules: list[dict]


_DEFAULT_BLOCKLIST_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "knowledge"
    / "risk"
    / "compliance_blocklist.md"
)

_RULES: Optional[list[BlocklistRule]] = None


def _normalise(value: str) -> str:
    return value.strip().lower()


def _parse_list(value: str) -> list[str]:
    return [_normalise(x) for x in value.split(",") if x.strip()]


def _field_value(section: str, field: str) -> str:
    """Extract the value of a **Field**: value pair from a section of markdown."""
    m = re.search(
        r"\*\*" + re.escape(field) + r"\*\*\s*:\s*(.+?)(?:\n|$)", section, re.IGNORECASE
    )
    return m.group(1).strip() if m else ""


def _parse_rules(markdown: str) -> list[BlocklistRule]:
    rules: list[BlocklistRule] = []
    sections = re.split(r"\n##\s+", markdown)
    for section in sections:
        if not section.strip():
            continue
        title_match = re.match(r"(?:Rule\s+\d+|Category)\s*:\s*(.+?)(?:\n|$)", section, re.IGNORECASE)
        if not title_match:
            continue
        title = title_match.group(1).strip()
        action = _field_value(section, "Action").lower()
        if not action:
            continue
        rule = BlocklistRule(
            title=title,
            categories=_parse_list(_field_value(section, "Categories")),
            subcategories=_parse_list(_field_value(section, "Subcategories")),
            keywords=_parse_list(_field_value(section, "Keywords")),
            platforms=_parse_list(_field_value(section, "Platforms")),
            action=action,
        )
        if rule.action == "block":
            rules.append(rule)
    return rules


def load_rules(blocklist_path: Optional[Path] = None) -> list[BlocklistRule]:
    path = blocklist_path or _DEFAULT_BLOCKLIST_PATH
    if not path.exists():
        raise FileNotFoundError(f"Blocklist not found: {path}")
    markdown = path.read_text(encoding="utf-8")
    return _parse_rules(markdown)


def _match_keywords(text: str, patterns: list[str]) -> bool:
    text_lower = text.lower()
    return any(pattern in text_lower for pattern in patterns)


def _match_keyword_list(keywords: list[str], patterns: list[str]) -> bool:
    return any(_match_keywords(kw, patterns) for kw in keywords)


def check_compliance(
    product: ProductIdentity,
    rules: Optional[list[BlocklistRule]] = None,
) -> ComplianceResult:
    global _RULES
    if rules is None:
        if _RULES is None:
            _RULES = load_rules()
        rules = _RULES

    matched: list[dict] = []
    for rule in rules:
        matched_categories = []
        matched_subcategories = []
        matched_keywords = []

        if rule.categories:
            for cat_pattern in rule.categories:
                if cat_pattern in product.category.lower():
                    matched_categories.append(cat_pattern)

        if rule.subcategories:
            for sub_pattern in rule.subcategories:
                if sub_pattern in product.subcategory.lower():
                    matched_subcategories.append(sub_pattern)

        if rule.keywords:
            for kw in product.normalized_keywords:
                for kw_pattern in rule.keywords:
                    if kw_pattern in kw.lower():
                        matched_keywords.append(kw_pattern)

        if matched_categories or matched_subcategories or matched_keywords:
            matched.append(
                {
                    "rule": rule.title,
                    "matched_categories": matched_categories,
                    "matched_subcategories": matched_subcategories,
                    "matched_keywords": matched_keywords,
                }
            )

    return ComplianceResult(flagged=len(matched) > 0, matched_rules=matched)
