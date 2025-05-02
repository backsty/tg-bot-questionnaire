import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
if os.path.exists(".env"):
    load_dotenv()
    logger.info("Загружены переменные из .env файла")
else:
    logger.info("Файл .env не найден, используем переменные окружения")

# Настройки бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.warning("BOT_TOKEN не найден в переменных окружения")

# Настройки подключения к PostgreSQL
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_DB = os.getenv("POSTGRES_DB", "quiz_bot")

# Для проверки наличия необходимых переменных
for var_name in ["POSTGRES_USER", "POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_PORT"]:
    logger.info(f"Переменная {var_name} = {os.getenv(var_name, 'не задана')}")

# Проверка режима отладки
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# URL для синхронного подключения (для alembic и других инструментов)
POSTGRES_URI = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

# URL для асинхронного подключения (для SQLAlchemy async)
DATABASE_URL = f"postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

# Логирование (без пароля)
logger.info(f"Конфигурация БД: {PG_USER}@{PG_HOST}:{PG_PORT}/{PG_DB}")