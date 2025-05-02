import os
from dotenv import load_dotenv

if os.path.exists(".env"):
  load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Настройки подключения к PostgreSQL
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = os.getenv("POSTGRES_PORT", 5432)
PG_DB = os.getenv("POSTGRES_DB", "quiz_bot")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

DATABASE_URL = f"postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"