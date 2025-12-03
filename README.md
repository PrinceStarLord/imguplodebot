# LookMyImg Telegram Uploader Bot

A Telegram bot that accepts images via DM, uploads them to **lookmyimg.com**, and replies **once** with all hosted links in **monospace** (code) format, separated by commas.  
Access is **restricted to admins** (default: your Telegram user ID `6167872503`).

## Features

- ✅ Upload a single image or a **media album** (bulk)
- ✅ Replies **once** per album with **comma-separated** hosted links
- ✅ Links are shown in **monospace** (Telegram `<code>…</code>`)
- ✅ Admin-only usage (configurable)
- ✅ Works with `X-API-Key` auth and `multipart/form-data` field `source`
- ✅ Cleans up temp files; robust JSON/regex URL extraction
- ✅ Clear error reporting (HTTP errors, DNS/connection, parse issues)

---

### Don't Forget to fill up .env file
---
---
##Demo Env.
```
API_ID=12345
API_HASH=jfefbi373jjehfhbu3r3bief
BOT_TOKEN=39473493:dhieufgbehfvegfvefeeg
LOOKMYIMG_API_KEY=cenkdjf783rbhsdc36efi&fheg728dferg
ADMIN_IDS = 483748484,3849475628
```
## Run the bot on VPS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```
