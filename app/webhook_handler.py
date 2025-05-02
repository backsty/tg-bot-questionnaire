import json
import logging
import asyncio
from aiogram import Bot, types
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import BOT_TOKEN
from app.handlers.common import register_common_handlers
from app.handlers.quiz import register_quiz_handlers

logger = logging.getLogger(__name__)

# Создаем экземпляры бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрируем обработчики
register_common_handlers(dp)
register_quiz_handlers(dp)


# Функция для обработки webhook-запросов
async def process_update(update_json):
    """Обрабатывает входящий запрос от Telegram API"""
    update = types.Update(**update_json)
    await dp.feed_update(bot, update)
    return {"status": "ok"}


# Для обработки в WSGI приложении
def handle_webhook(update_data):
    """Обрабатывает webhook-запрос в синхронном контексте"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(process_update(update_data))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}