import os
from pathlib import Path
from dotenv import load_dotenv

# Repo root, so every path below works no matter which directory the app is started from
PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / "config.env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UNPROCESSED_FOLDER_ID = os.getenv("UNPROCESSED_FOLDER_ID")
PROCESSED_FOLDER_ID = os.getenv("PROCESSED_FOLDER_ID")
SERVICE_ACCOUNT_FILE = PROJECT_ROOT / os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service-account-key.json")
