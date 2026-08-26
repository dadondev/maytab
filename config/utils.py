from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")
DB_URL = os.getenv("DB_URL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
# Bot owner chat id — automatically made admin on startup.
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID", "")

# Webhook settings (only used if WEBHOOK_USE is truthy)
WEBHOOK_USE = os.getenv("WEBHOOK_USE", "0") in ("1", "true", "True", "yes")
WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN", "")  # e.g. https://example.com
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
# Telegram's secret token only allows A-Z, a-z, 0-9, _ and -.
# Sanitize so an invalid value (e.g. containing '@') can't crash set_webhook.
WEBHOOK_SECRET = "".join(
    c for c in os.getenv("WEBHOOK_SECRET", "") if c.isalnum() or c in "_-"
)
# Railway/other PaaS inject the TCP port via the PORT env var — fall back to it.
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT") or os.getenv("PORT") or "8080")


# REGEX
admit_task_regex = r"^admit_task_date:(?:edit|accept)(?::\d+)?$"