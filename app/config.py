import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env если файл существует
if os.path.exists(".env"):
    load_dotenv()
    logger.info("Загружены переменные из .env файла")
else:
    logger.info("Файл .env не найден, используем переменные окружения")

# Настройки бота
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.warning("BOT_TOKEN не найден в переменных окружения")

# Настройки подключения к PostgreSQL
PG_USER = os.environ.get("POSTGRES_USER", "postgres")
PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")
PG_HOST = os.environ.get("POSTGRES_HOST", "localhost")
PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
PG_DB = os.environ.get("POSTGRES_DB", "quiz_bot")
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# Выводим переменные в лог для проверки
logger.info(f"Переменная POSTGRES_USER = {os.environ.get('POSTGRES_USER', 'не задана')}")
logger.info(f"Переменная POSTGRES_HOST = {os.environ.get('POSTGRES_HOST', 'не задана')}")
logger.info(f"Переменная POSTGRES_DB = {os.environ.get('POSTGRES_DB', 'не задана')}")
logger.info(f"Переменная POSTGRES_PORT = {os.environ.get('POSTGRES_PORT', 'не задана')}")

# Проверяем значения и логируем (без вывода пароля)
logger.info(f"Конфигурация БД: {PG_USER}@{PG_HOST}:{PG_PORT}/{PG_DB}")

# Формируем URL для подключения
DATABASE_URL = f"postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"