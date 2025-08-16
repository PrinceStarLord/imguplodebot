# LookMyImg Telegram Uploader Bot (Pyrogram v2)

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

## Demo (Response Format)

