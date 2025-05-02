from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

import os
import logging
from app.config import BOT_TOKEN

logger = logging.getLogger(__name__)

# Проверка наличия токена бота
if not BOT_TOKEN:
    logger.critical("BOT_TOKEN не найден в переменных окружения!")
    raise ValueError("Не указан токен бота. Проверьте переменные окружения.")

# Инициализация бота и диспетчера
try:
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    logger.info("Бот и диспетчер успешно инициализированы")
except Exception as e:
    logger.error(f"Ошибка при инициализации бота: {e}")
    raise

# Функция для создания и настройки диспетчера
def create_dispatcher():
    """Функция для создания диспетчера с нужными настройками"""
    try:
        from app.middlewares.throttling import ThrottlingMiddleware
        
        # Регистрация middleware для ограничения запросов
        dp.message.middleware(ThrottlingMiddleware())
        dp.callback_query.middleware(ThrottlingMiddleware())
        
        logger.info("Middleware успешно зарегистрированы")
        return dp
    except ImportError as e:
        logger.error(f"Ошибка при импорте middleware: {e}")
        return dp
    except Exception as e:
        logger.error(f"Ошибка при регистрации middleware: {e}")
        return dp