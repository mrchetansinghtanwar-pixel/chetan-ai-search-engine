"""Gemini image generation; credentials stay server-side."""
import base64
import binascii
from agent import generate, GeminiError


def create_image(api_key, model, prompt, style, ratio):
    if not prompt.strip():
        raise GeminiError("Enter an image description first.")
    if ratio not in {"1:1", "16:9", "9:16"}:
        raise GeminiError("Invalid image size.")
    data = generate(api_key, model, {
        "contents": [{"role": "user", "parts": [{"text":
            f"Create an image. Style: {style}. User description: {prompt[:4000]}"}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"],
                             "imageConfig": {"aspectRatio": ratio}},
    })
    images, notes = [], []
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if part.get("thought"):
                continue
            if part.get("text"):
                notes.append(part["text"])
            inline = part.get("inlineData", {})
            mime = inline.get("mimeType", "")
            if mime in {"image/png", "image/jpeg", "image/webp"} and inline.get("data"):
                try:
                    blob = base64.b64decode(inline["data"], validate=True)
                except (ValueError, binascii.Error):
                    raise GeminiError("Could not read image data. Please try again.") from None
                if blob:
                    images.append({"data": blob, "mime": mime})
    if not images:
        raise GeminiError("No image was returned. Try a different prompt and check model access and quota.")
    return {"images": images, "notes": "\n".join(notes), "prompt": prompt}


def create_cloudflare_image(token, account_id, prompt, style):
    import re
    import requests
    if not token or not re.fullmatch(r"[a-fA-F0-9]{32}", account_id):
        raise GeminiError("Save a Cloudflare API token and valid Account ID in secrets.")
    if not prompt.strip():
        raise GeminiError("Enter an image description first.")
    try:
        response = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell",
            headers={"Authorization": f"Bearer {token}"},
            json={"prompt": f"Style: {style}. {prompt}"[:2048], "steps": 4},
            timeout=(10, 90),
        )
    except requests.RequestException:
        raise GeminiError("Cloudflare connection timed out. Please try again.") from None
    if response.status_code in (401, 403):
        raise GeminiError("Check your Cloudflare token, account and Workers AI permissions.")
    if response.status_code == 429:
        raise GeminiError("Cloudflare quota or rate limit reached. Check your usage dashboard.")
    if response.status_code != 200:
        raise GeminiError("Cloudflare image request failed. Please try again later.")
    try:
        data = response.json()
        if not data.get("success", True):
            raise ValueError()
        encoded = data.get("result", {}).get("image", "")
        blob = base64.b64decode(encoded, validate=True)
        if not blob:
            raise ValueError()
    except (ValueError, TypeError, AttributeError, binascii.Error):
        raise GeminiError("Cloudflare did not return a valid image.") from None
    return {"images": [{"data": blob, "mime": "image/jpeg"}], "notes": "", "prompt": prompt}
