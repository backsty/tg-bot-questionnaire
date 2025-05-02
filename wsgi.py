import logging
import sys
import os
from dotenv import load_dotenv
import threading
import time
import asyncio

# Загружаем переменные окружения
if os.path.exists(".env"):
    load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def app(environ, start_response):
    """Простой WSGI-интерфейс для Gunicorn"""
    status = '200 OK'
    headers = [('Content-type', 'text/plain')]
    start_response(status, headers)
    
    # Проверяем, запущен ли бот
    bot_status = "running" if os.environ.get('BOT_ALREADY_RUNNING') else "not running"
    logger.info(f"Bot status: {bot_status}")
    return [f"Telegram bot is {bot_status}".encode()]


# Модифицированная версия запуска бота без сигналов
def run_bot():
    try:
        logger.info("Запуск бота в процессе Gunicorn")
        
        # Импортируем только необходимые компоненты
        from app.config import BOT_TOKEN, PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DB
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from aiogram.dispatcher.dispatcher import Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        
        # Проверяем наличие переменных окружения
        if not all([BOT_TOKEN, PG_USER, PG_PASSWORD, PG_DB, PG_HOST]):
            missing_vars = []
            if not BOT_TOKEN: missing_vars.append("BOT_TOKEN")
            if not PG_USER: missing_vars.append("POSTGRES_USER")
            if not PG_PASSWORD: missing_vars.append("POSTGRES_PASSWORD")
            if not PG_DB: missing_vars.append("POSTGRES_DB")
            if not PG_HOST: missing_vars.append("POSTGRES_HOST")
            
            logger.error(f"Отсутствуют необходимые переменные окружения: {', '.join(missing_vars)}")
            return
        
        # Создаём простой поллинг без сигналов
        async def polling():
            try:
                # Создаем бота с базовыми параметрами
                bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
                dp = Dispatcher(storage=MemoryStorage())
                
                # Регистрируем базовые обработчики
                from app.handlers.common import register_common_handlers
                register_common_handlers(dp)
                
                # Настройка базы данных
                from app.database.engine import engine
                from app.database.base import Base
                
                # Создаем структуру базы данных
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                logger.info(f"Таблицы базы данных созданы на {PG_HOST}")
                
                # Настраиваем команды бота
                from aiogram.types import BotCommand
                await bot.set_my_commands([
                    BotCommand(command="start", description="Запустить бота"),
                    BotCommand(command="help", description="Помощь по использованию"),
                    BotCommand(command="quiz", description="Начать тест")
                ])
                
                logger.info("Запускаем поллинг бота в безопасном режиме")
                # Запускаем поллинг в бесконечном цикле
                while True:
                    try:
                        await dp.start_polling(bot, allowed_updates=["message", "callback_query"], skip_updates=True)
                    except Exception as e:
                        logger.error(f"Ошибка в цикле поллинга: {e}")
                        # Пауза перед повторной попыткой
                        await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Критическая ошибка при запуске бота: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        # Создаем новый цикл событий
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Запускаем поллинг без обработки сигналов
        loop.run_until_complete(polling())
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())


# Запускаем бот в отдельном потоке
def start_bot_thread():
    if not os.environ.get('BOT_ALREADY_RUNNING'):
        os.environ['BOT_ALREADY_RUNNING'] = 'True'
        logger.info("Запуск потока с ботом")
        # Запускаем бота в daemon-потоке
        thread = threading.Thread(target=run_bot, daemon=True)
        thread.start()
        logger.info("Бот запущен в отдельном потоке")
        return thread
    else:
        logger.info("Бот уже запущен")
        return None


# Запускаем бот при импорте модуля
bot_thread = start_bot_thread()