import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from app.config import BOT_TOKEN, DEBUG

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
try:
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    logger.info(f"Бот инициализирован с токеном: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}")
except Exception as e:
    logger.error(f"Ошибка при инициализации бота: {e}")
    raise

# Функция для регистрации всех middleware
def create_dispatcher():
    try:
        from app.middlewares.throttling import ThrottlingMiddleware
        
        # Регистрация middleware для ограничения запросов
        dp.message.middleware(ThrottlingMiddleware())
        dp.callback_query.middleware(ThrottlingMiddleware())
        
        logger.info("Middleware успешно зарегистрированы")
        
    except Exception as e:
        logger.error(f"Ошибка при регистрации middleware: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return dp