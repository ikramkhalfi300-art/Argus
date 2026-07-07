from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


class ScrapedPage:
    def __init__(self, url: str, title: str = "", price: str = "",
                 images: list[str] | None = None,
                 description: str = "",
                 variants: list[str] | None = None,
                 html_text: str = ""):
        self.url = url
        self.title = title
        self.price = price
        self.images = images or []
        self.description = description
        self.variants = variants or []
        self.html_text = html_text


async def scrape_product_page(url: str, timeout: float = 15.0) -> ScrapedPage:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url, headers={
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/131.0.0.0 Safari/537.36"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    title = _extract_title(soup)
    price = _extract_price(soup)
    images = _extract_images(soup, url)
    description = _extract_description(soup)
    variants = _extract_variants(soup)

    return ScrapedPage(
        url=url,
        title=title,
        price=price,
        images=images,
        description=description,
        variants=variants,
        html_text=html,
    )


def _extract_title(soup: BeautifulSoup) -> str:
    candidates = [
        soup.find("meta", property="og:title"),
        soup.find("meta", property="twitter:title"),
        soup.find("h1"),
        soup.find("title"),
    ]
    for el in candidates:
        if el and (content := el.get("content") or el.get_text(strip=True)):
            return content
    return ""


def _extract_price(soup: BeautifulSoup) -> str:
    candidates = [
        soup.find("meta", property="product:price:amount"),
        soup.find("meta", property="og:price:amount"),
        *soup.find_all("span", class_=lambda c: c and "price" in c.lower() if c else False),
        *soup.find_all("div", class_=lambda c: c and "price" in c.lower() if c else False),
    ]
    for el in candidates:
        if el and (content := el.get("content") or el.get_text(strip=True)):
            cleaned = "".join(c for c in content if c.isdigit() or c in ".,$€£¥")
            if cleaned:
                return cleaned
    return ""


def _extract_images(soup: BeautifulSoup, base_url: str) -> list[str]:
    urls: list[str] = []
    candidates = [
        soup.find("meta", property="og:image"),
        soup.find("meta", property="twitter:image"),
        *soup.find_all("img", class_=lambda c: c and any(k in (c or "").lower()
                      for k in ("main", "hero", "primary", "product")) if c else False),
        *soup.find_all("img", {"data-image": True}),
        *soup.select("[data-testid='product-image'] img"),
        *soup.select("[data-testid='product-image']"),
        *soup.find_all("img", src=True),
    ]
    seen: set[str] = set()
    for el in candidates:
        if not hasattr(el, "get"):
            continue
        src = (el.get("content") or el.get("src") or el.get("data-image") or "").strip()
        if not src or src.startswith("data:"):
            continue
        if src.startswith("//"):
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            src = f"{parsed.scheme}:{src}"
        elif src.startswith("/"):
            from urllib.parse import urljoin
            src = urljoin(base_url, src)
        if src not in seen:
            seen.add(src)
            urls.append(src)
    return urls[:5]


def _extract_description(soup: BeautifulSoup) -> str:
    candidates = [
        soup.find("meta", property="og:description"),
        soup.find("meta", attrs={"name": "description"}),
        soup.find("meta", property="twitter:description"),
        soup.find("div", class_=lambda c: c and any(k in (c or "").lower()
                  for k in ("desc", "product-info")) if c else False),
        soup.find("p", class_=lambda c: c and "desc" in (c or "").lower() if c else False),
    ]
    for el in candidates:
        if el and (content := el.get("content") or el.get_text(strip=True)):
            return content[:2000]
    return ""


def _extract_variants(soup: BeautifulSoup) -> list[str]:
    variants: list[str] = []
    selectors = [
        "select[data-testid='variant-selector'] option",
        "select[name='variants'] option",
        ".variant-selector option",
        ".product-variants option",
        "[data-variant]",
        ".variant-button",
        ".swatch",
    ]
    for sel in selectors:
        for el in soup.select(sel):
            text = el.get_text(strip=True) or el.get("data-variant") or el.get("value") or ""
            if text and text not in variants:
                variants.append(text)
        if variants:
            break
    for ul in soup.find_all("ul", class_=lambda c: c and "variant" in (c or "").lower() if c else False):
        for li in ul.find_all("li"):
            text = li.get_text(strip=True)
            if text and text not in variants:
                variants.append(text)
    return variants[:20]
