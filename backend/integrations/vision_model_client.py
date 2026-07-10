"""Image download utility for Claude vision.

Downloads a product image from a URL and returns (media_type, base64_data)
suitable for passing as an image content block in the Anthropic Messages API.

This is the real implementation — not a stub.  In Sprint 4.1.1 / 5.2.1 this
could be extended to also support file:// paths, local files, or a dedicated
vision-preprocessing pipeline.
"""

import base64

import httpx


class ImageDownloadError(Exception):
    """Raised when the image cannot be downloaded or its format is unsupported."""


SUPPORTED_MEDIA_TYPES = {
    "image/jpeg": True,
    "image/png": True,
    "image/gif": True,
    "image/webp": True,
}


async def download_image(image_url: str, timeout: float = 15.0) -> tuple[str, str]:
    """Download an image from *image_url* and return (media_type, base64_data).

    Raises
    ------
    ImageDownloadError
        If the download fails, the response is not an image, or the media type
        is not supported by the Anthropic API (JPEG / PNG / GIF / WebP only).
    """
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(
            image_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            },
        )
        resp.raise_for_status()

    content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
    if not content_type.startswith("image/"):
        raise ImageDownloadError(
            f"URL did not return an image (content-type: {content_type!r})"
        )
    if content_type not in SUPPORTED_MEDIA_TYPES:
        raise ImageDownloadError(
            f"Unsupported image type {content_type!r}; "
            f"must be one of {list(SUPPORTED_MEDIA_TYPES)}"
        )

    b64 = base64.b64encode(resp.content).decode("ascii")
    return content_type, b64
