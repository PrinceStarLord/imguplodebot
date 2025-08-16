LookMyImg Telegram Uploader Bot (Pyrogram v2)

A Telegram bot that accepts images via DM, uploads them to lookmyimg.com, and replies once with all hosted links in monospace (code) format, separated by commas.
Access is restricted to admins (default: your Telegram user ID 6167872503).

Features

✅ Upload a single image or a media album (bulk)

✅ Replies once per album with comma-separated hosted links

✅ Links are shown in monospace (Telegram <code>…</code>)

✅ Admin-only usage (configurable)

✅ Works with X-API-Key auth and multipart/form-data field source

✅ Cleans up temp files; robust JSON/regex URL extraction

✅ Clear error reporting (HTTP errors, DNS/connection, parse issues)

Demo (Response Format)
Uploaded successfully!
`https://lookmyimg.com/images/2025/08/16/a.jpeg, https://lookmyimg.com/images/2025/08/16/b.jpeg, https://lookmyimg.com/images/2025/08/16/c.jpeg`


(Using HTML <code>…</code> under the hood so the entire line is mono.)

Requirements

Python 3.10+ (tested with 3.12)

Telegram Bot token

LookMyImg API key

Packages:

pyrogram tgcrypto aiohttp python-dotenv

Install:

pip install -U pyrogram tgcrypto aiohttp python-dotenv

Getting Started
1) Create a Telegram Bot

Talk to @BotFather → /newbot → get BOT_TOKEN.

2) Collect LookMyImg API Info

API key

Upload endpoint (defaults to https://lookmyimg.com/api/1/upload)

Example cURL from LookMyImg docs:

curl --fail-with-body -X POST \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: multipart/form-data" \
  -F "source=@image.jpeg" \
  https://lookmyimg.com/api/1/upload

3) Configure environment

Create a .env file in the project root:

API_ID=123456
API_HASH=your_api_hash
BOT_TOKEN=123456:ABC-your-bot-token

LOOKMYIMG_API_KEY=your_lookmyimg_api_key
LOOKMYIMG_ENDPOINT=https://lookmyimg.com/api/1/upload

# Optional overrides:
# FORM_FILE_FIELD=source
# EXTRA_FORM_FIELDS={}              # e.g. {"folder":"telegram"}  (JSON)
# MAX_FILE_MB=30
# ADMIN_IDS=6167872503              # comma-separated user IDs if multiple admins


Don’t know your API_ID/API_HASH? Create a developer account at https://my.telegram.org and generate them.

4) Run the bot
python3 lookmyimg_bot.py


You should see startup logs, then “Session started”.

Usage

DM the bot a photo or image document (.jpg, .jpeg, .png, .webp, .gif, .bmp).

To upload multiple images, send an album (media group). The bot collects all images and replies once with all hosted links in one monospace line separated by commas.

Configuration & Behavior
Setting	Source	Default	Notes
LOOKMYIMG_ENDPOINT	.env	https://lookmyimg.com/api/1/upload	Must accept multipart/form-data with field source
LOOKMYIMG_API_KEY	.env	—	Sent as X-API-Key header
FORM_FILE_FIELD	.env	source	Change only if your API expects a different field name
EXTRA_FORM_FIELDS	.env (JSON)	{}	Extra form fields, e.g. {"folder":"telegram"}
ADMIN_IDS	.env	6167872503	Comma-separated Telegram user IDs
MAX_FILE_MB	.env	30	Client-side validation only
Allowed formats	code	.jpg .jpeg .png .webp .gif .bmp
