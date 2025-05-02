import asyncio
import logging
import sys
import os
import signal
from dotenv import load_dotenv
from aiogram.types import BotCommand

# Загружаем переменные окружения
if os.path.exists(".env"):
    load_dotenv()

# Импортируем компоненты бота
from app.bot import dp, bot
from app.handlers.common import register_common_handlers
from app.handlers.quiz import register_quiz_handlers
from app.database.engine import engine
from app.database.base import Base

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Регистрация обработчиков
register_common_handlers(dp)
register_quiz_handlers(dp)


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

    # Устанавливаем команды бота
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Помощь по использованию"),
        BotCommand(command="quiz", description="Начать тест")
    ])

    # Логируем настройки подключения к БД (без паролей)
    db_host = os.environ.get('POSTGRES_HOST', 'localhost')
    db_name = os.environ.get('POSTGRES_DB', 'quiz_bot')
    logger.info(f"Подключено к БД {db_name} на хосте {db_host}")
    
    logger.info(f"Бот запущен в режиме поллинга")


# Функция при завершении работы бота
async def on_shutdown():
    logger.info("Закрытие соединения с базой данных...")
    await engine.dispose()
    logger.info("Соединение с базой данных закрыто")
    logger.info("Бот остановлен")


# Обработчик сигналов для корректного завершения на Render
def signal_handler(sig, frame):
    logger.info("Получен сигнал завершения, останавливаем бота...")
    sys.exit(0)


async def main():
    try:
        # Устанавливаем обработчики запуска и остановки
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        # На Render нужно обрабатывать сигналы завершения
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Запускаем бота с поллингом
        logger.info("Начинаем поллинг...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())