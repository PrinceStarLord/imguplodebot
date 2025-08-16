import asyncio
import json
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional
from html import escape
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
import aiohttp

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

LOOKMYIMG_ENDPOINT = os.getenv("LOOKMYIMG_ENDPOINT", "https://lookmyimg.com/api/1/upload")
LOOKMYIMG_API_KEY = os.getenv("LOOKMYIMG_API_KEY", "")

FORM_FILE_FIELD = os.getenv("FORM_FILE_FIELD", "source")
EXTRA_FORM_FIELDS = json.loads(os.getenv("EXTRA_FORM_FIELDS", "{}"))

ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
MAX_FILE_MB = float(os.getenv("MAX_FILE_MB", "30"))

ADMIN_ID = 6167872503

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("lookmyimg-bot")

# Deduplicate media groups (albums) so we reply once per album
PROCESSED_MEDIA_GROUPS: set[str] = set()

async def _expire_media_group(gid: str, ttl: int = 180):
    await asyncio.sleep(ttl)
    PROCESSED_MEDIA_GROUPS.discard(gid)

def _build_headers() -> dict:
    return {"X-API-Key": LOOKMYIMG_API_KEY}

async def _raise_for_status(resp: aiohttp.ClientResponse):
    if 200 <= resp.status < 300:
        return
    text = await resp.text()
    raise aiohttp.ClientResponseError(
        request_info=resp.request_info,
        history=resp.history,
        status=resp.status,
        message=text,
        headers=resp.headers,
    )

@asynccontextmanager
async def _aiohttp_session():
    import socket
    timeout = aiohttp.ClientTimeout(total=180)
    connector = aiohttp.TCPConnector(limit=100, family=socket.AF_INET)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector, trust_env=True) as session:
        yield session

def _extract_url(data: Any) -> Optional[str]:
    # Prioritize common JSON locations
    if isinstance(data, dict):
        for path in (["url"], ["link"], ["data","url"], ["image","url"], ["result","url"], ["result","link"]):
            cur = data
            ok = True
            for k in path:
                if isinstance(cur, dict) and k in cur:
                    cur = cur[k]
                else:
                    ok = False
                    break
            if ok and isinstance(cur, str):
                return cur
        images = data.get("images") if isinstance(data, dict) else None
        if isinstance(images, list) and images:
            for key in ("url","link","src"):
                v = images[0].get(key) if isinstance(images[0], dict) else None
                if isinstance(v, str):
                    return v
    # Fallback regex (generic)
    try:
        text = json.dumps(data)
    except Exception:
        text = str(data)
    import re
    m = re.search(r'https?://[^\s"\'<>]+', text)
    return m.group(0) if m else None

async def upload_to_lookmyimg(local_path: Path) -> str:
    headers = _build_headers()
    form = aiohttp.FormData()
    for k, v in EXTRA_FORM_FIELDS.items():
        form.add_field(k, str(v))

    form.add_field(
        name=FORM_FILE_FIELD,
        value=open(local_path, "rb"),
        filename=local_path.name,
        content_type="application/octet-stream",
    )

    async with _aiohttp_session() as session:
        async with session.post(LOOKMYIMG_ENDPOINT, headers=headers, data=form) as resp:
            await _raise_for_status(resp)
            ct = resp.headers.get("Content-Type", "")
            if "application/json" in ct:
                data = await resp.json(content_type=None)
            else:
                body = await resp.text()
                try:
                    data = json.loads(body)
                except Exception:
                    data = body

    url = _extract_url(data)
    if not url:
        logger.error("Upload OK but no URL in response: %s", data)
        raise RuntimeError("Upload succeeded but URL not found in response.")
    return url

app = Client(
    name="lookmyimg_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir=str(Path(__file__).parent),
)

@app.on_message(filters.command(["start","help"]) & filters.private)
async def start_handler(_: Client, m: Message):
    if not m.from_user or m.from_user.id != ADMIN_ID:
        return await m.reply_text("Access denied. You are not authorized to use this bot.")
    text = (
        "Send me one or more *photos* or *image files* and I'll upload them to LookMyImg and reply with the link(s).\n\n"
        "If you send multiple images at once, you'll get a single message with all links separated by commas.\n\n"
        f"Supported formats: {', '.join(sorted(ext.strip('.') for ext in ALLOWED_EXTS)).upper()}. "
        f"Max size: ~{int(MAX_FILE_MB)} MB.\n\n"
        "Admin notes: set API creds in `.env`."
    )
    await m.reply_text(text, disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN)

async def _download_to_temp(c: Client, m: Message) -> Path:
    tempdir = Path(tempfile.mkdtemp(prefix="lookmyimg_"))
    if m.photo:
        suggested = f"{m.photo.file_unique_id}.jpg"
    else:
        suggested = m.document.file_name or f"{m.document.file_unique_id}"
    local = tempdir / suggested
    await c.download_media(message=m, file_name=str(local))
    return local

def _validate_image(path: Path):
    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: {sorted(ALLOWED_EXTS)}")
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_MB:
        raise ValueError(f"File too large: {size_mb:.1f} MB > {MAX_FILE_MB} MB")

@app.on_message((filters.photo | filters.document) & filters.private)
async def image_handler(c: Client, m: Message):
    if not m.from_user or m.from_user.id != ADMIN_ID:
        return await m.reply_text("Access denied. You are not authorized to use this bot.")

    try:
        # Prevent duplicate replies for the same album
        if m.media_group_id:
            gid = str(m.media_group_id)
            if gid in PROCESSED_MEDIA_GROUPS:
                return
            PROCESSED_MEDIA_GROUPS.add(gid)
            asyncio.create_task(_expire_media_group(gid))

        # Collect album messages or single
        messages = await c.get_media_group(m.chat.id, m.id) if m.media_group_id else [m]

        notice = await m.reply_text("Processing image(s)…")

        urls = []
        for msg in messages:
            if msg.document and (msg.document.mime_type or "").startswith("video/"):
                continue
            local_path = await _download_to_temp(c, msg)
            _validate_image(local_path)
            url = await upload_to_lookmyimg(local_path)
            urls.append(url)
            try:
                if local_path.exists():
                    for p in local_path.parent.iterdir():
                        p.unlink(missing_ok=True)
                    local_path.parent.rmdir()
            except Exception:
                pass

        if not urls:
            return await notice.edit_text("No image files found in that message/album.")

        # Show ALL links inside a single monospace block, including commas
        links_text = "<code>" + escape(", ".join(urls)) + "</code>"

        await notice.edit_text(
            "<b>Uploaded successfully ❤️\n\n" + links_text,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML,
        )

    except aiohttp.ClientResponseError as e:
        logger.exception("HTTP error during upload")
        details = getattr(e, "message", str(e))
        await m.reply_text(
            "Upload failed with an HTTP error.\n"
            f"Status: {e.status}\n"
            f"Details: {details[:500]}"
        )
    except (aiohttp.ClientConnectorDNSError, aiohttp.ClientConnectorError) as e:
        logger.exception("Network/DNS error")
        await m.reply_text(
            "Network error while connecting to LookMyImg. This usually means DNS could not resolve the API host or outbound internet is blocked on the server.\n\n"
            "Try: 1) Verify LOOKMYIMG_ENDPOINT host, 2) Check DNS on server (dig +short <hostname>), 3) Force IPv4 or set a public resolver like 1.1.1.1/8.8.8.8, 4) Ensure firewall allows HTTPS egress.\n\n"
            f"Details: {type(e).__name__}: {e}"
        )
    except Exception as e:
        logger.exception("General error")
        await m.reply_text(f"Sorry, something went wrong: {e}")

if __name__ == "__main__":
    missing = []
    if not API_ID: missing.append("API_ID")
    if not API_HASH: missing.append("API_HASH")
    if not BOT_TOKEN: missing.append("BOT_TOKEN")
    if not LOOKMYIMG_API_KEY: missing.append("LOOKMYIMG_API_KEY")
    if missing:
        print("Missing required env vars:", ", ".join(missing))
        print("Create a .env file as shown at the top of this script.")
        raise SystemExit(1)

    app.run()
