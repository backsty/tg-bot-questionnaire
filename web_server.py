import asyncio
import logging
import os
import threading
import signal
from dotenv import load_dotenv
from aiohttp import web

# Импортируем компоненты бота
from app.bot import dp, bot
from app.handlers.common import register_common_handlers
from app.handlers.quiz import register_quiz_handlers
from app.database.engine import engine
from app.database.base import Base

# Загружаем переменные окружения
if os.path.exists(".env"):
    load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получаем порт из переменной окружения (Render предоставляет PORT)
PORT = int(os.environ.get("PORT", 10000))


# Функция удаления webhook перед запуском
async def remove_webhook():
    """Удаляет webhook перед запуском поллинга"""
    logger.info("Проверка и удаление webhook...")
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url:
        logger.info(f"Найден активный webhook: {webhook_info.url}")
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Webhook удален")
    else:
        logger.info("Webhook не настроен, запуск в режиме поллинга")


# Функция создания таблиц базы данных при запуске
async def on_startup():
    # Всегда удаляем webhook для корректной работы поллинга
    await remove_webhook()
    
    logger.info("Создание таблиц в базе данных...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Таблицы базы данных созданы")
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info(f"Бот запущен в режиме поллинга")


# Функция при завершении работы бота
async def on_shutdown():
    logger.info("Закрытие соединения с базой данных...")
    await engine.dispose()
    logger.info("Соединение с базой данных закрыто")
    logger.info("Бот остановлен")


async def start_polling():
    """Запуск бота в режиме поллинга"""
    # Регистрация обработчиков
    register_common_handlers(dp)
    register_quiz_handlers(dp)
    
    # Устанавливаем обработчики запуска и остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запускаем бота с поллингом
    logger.info("Начинаем поллинг...")
    await dp.start_polling(bot)


def run_bot():
    """Запуск бота в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_polling())
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        loop.close()


async def health_check(request):
    """Эндпоинт для проверки работоспособности сервиса"""
    # Обратите внимание, что бот работает независимо от этого эндпоинта
    return web.Response(text="Telegram bot is running!")


async def on_startup_app(app):
    """Функция, которая выполняется при запуске веб-сервера"""
    logger.info(f"Веб-сервер запущен на порту {PORT}")


def main():
    """Основная функция для запуска веб-сервера и бота"""
    # Запускаем бот в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("Бот запущен в отдельном потоке")
    
    # Создаем веб-приложение
    app = web.Application()
    
    # Добавляем маршруты
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    # Обработчик сигналов для корректного завершения
    def signal_handler(sig, frame):
        logger.info("Получен сигнал завершения, останавливаем сервис...")
        asyncio.get_event_loop().stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Запускаем веб-сервер
    app.on_startup.append(on_startup_app)
    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()