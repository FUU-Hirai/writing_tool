import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["OPENAI_MODEL"] = "test-model"

from app.config import get_settings

get_settings.cache_clear()
