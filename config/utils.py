from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")
DB_URL = os.getenv("DB_URL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


# REGEX
admit_task_regex = r"^admit_task_date:(?:edit|accept)(?::\d+)?$"