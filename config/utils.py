from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")
DB_URL = os.getenv("DB_URL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# Webhook settings (only used if WEBHOOK_USE is truthy)
WEBHOOK_USE = os.getenv("WEBHOOK_USE", "0") in ("1", "true", "True", "yes")
WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN", "")  # e.g. https://example.com
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8443"))


# REGEX
admit_task_regex = r"^admit_task_date:(?:edit|accept)(?::\d+)?$"