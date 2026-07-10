"""
Reverse-image-search integration for finding visually similar products.

============================================================================
SPRINT 1.1.3 NOTE: This is a STUB.  No real reverse-image-search service has
been integrated.  Basic product identification from images is handled by
Claude's native vision capability in discovery_agent.py.  Reverse-image-
search-by-similarity is a separate future feature.
============================================================================
"""
# TODO: Replace with real reverse-image-search integration in Sprint 4.1.1 / 5.2.1


SEARCH_KEYWORDS: dict[str, list[str]] = {
    "headphone": ["Sony WH-1000XM5 headphones", "wireless noise cancelling headphones"],
    "speaker": ["bluetooth speaker portable", "waterproof speaker"],
    "shoe": ["Nike running shoes", "athletic footwear"],
    "bag": ["leather backpack", "travel duffel bag"],
    "watch": ["smartwatch fitness tracker", "analog wrist watch"],
    "camera": ["digital camera", "mirrorless camera body"],
    "keyboard": ["mechanical keyboard", "ergonomic keyboard"],
    "tent": ["camping tent 4 person", "waterproof tent rainfly"],
    "coat": ["winter wool coat", "women long coat"],
    "tea": ["matcha green tea", "ceremonial grade matcha"],
}


async def search_by_image(image_url: str) -> list[dict]:
    """Given an image URL, return candidate product descriptions.

    Stub implementation — infers keywords from the URL itself and returns
    canned matches.  Replace with a real reverse-image-search API call.
    """
    keywords_found: list[str] = []
    url_lower = image_url.lower()
    for keyword, candidates in SEARCH_KEYWORDS.items():
        if keyword in url_lower:
            keywords_found.extend(candidates)
    if not keywords_found:
        keywords_found = ["similar product", "related item"]
    return [{"title": kw, "source": "reverse_image_search (stub)"} for kw in keywords_found]
