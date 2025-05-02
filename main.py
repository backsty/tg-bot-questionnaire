import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram.types import BotCommand

# Загрузка переменных окружения
if os.path.exists(".env"):
    load_dotenv()

from app.bot import bot, dp, create_dispatcher
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

# Снижаем уровень логирования для SQLAlchemy, чтобы уменьшить число записей
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

# Инициализируем middleware
create_dispatcher()

# Регистрация обработчиков
register_common_handlers(dp)
register_quiz_handlers(dp)


# Функция создания таблиц базы данных при запуске
async def on_startup():
    try:
        logger.info("Создание таблиц в базе данных...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Таблицы базы данных созданы")

        # Устанавливаем команды бота
        await bot.set_my_commands([
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="help", description="Помощь по использованию"),
            BotCommand(command="quiz", description="Начать тест")
        ])

        # Логируем настройки подключения к БД (без паролей)
        db_host = os.environ.get('POSTGRES_HOST', 'не задан')
        db_name = os.environ.get('POSTGRES_DB', 'не задан')
        logger.info(f"Подключено к БД {db_name} на хосте {db_host}")
        
        logger.info("Бот запущен")
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")
        import traceback
        logger.error(traceback.format_exc())


# Функция при завершении работы бота
async def on_shutdown():
    try:
        logging.info("Закрытие соединения с базой данных...")
        await engine.dispose()
        logging.info("Соединение с базой данных закрыто")
    except Exception as e:
        logger.error(f"Ошибка при завершении работы: {e}")
    finally:
        logging.info("Бот остановлен")


async def main():
    try:
        # Устанавливаем обработчики запуска и остановки
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)

        # Запускаем бота
        logger.info("Начинаем поллинг...")
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        import traceback
        logging.error(traceback.format_exc())