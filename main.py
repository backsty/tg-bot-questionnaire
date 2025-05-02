import asyncio
import logging
import sys
import os
from aiogram.types import BotCommand
from dotenv import load_dotenv

# Загружаем переменные окружения из .env если мы запускаемся локально
if os.path.exists(".env"):
    load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from app.bot import dp, bot
    from app.handlers.common import register_common_handlers
    from app.handlers.quiz import register_quiz_handlers
    from app.database.engine import engine
    from app.database.base import Base

    # Логируем информацию о доступных переменных окружения (без вывода значений)
    env_vars = ["BOT_TOKEN", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_HOST", "POSTGRES_PORT"]
    logger.info(f"Проверка переменных окружения: " + 
                ", ".join([f"{var}: {'✓' if os.environ.get(var) else '✗'}" for var in env_vars]))
    
    # Регистрация обработчиков
    register_common_handlers(dp)
    register_quiz_handlers(dp)
except ImportError as e:
    logger.error(f"Ошибка импорта: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Ошибка при настройке: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)


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

        # Только первые 5 символов токена для логов
        token_prefix = os.environ.get("BOT_TOKEN", "")[:5] + "..." if os.environ.get("BOT_TOKEN") else "Не найден"
        logger.info(f"Бот запущен с токеном {token_prefix}")
        
        # Показываем в логах где мы запущены
        environment = "Render" if os.environ.get("RENDER") else "Локально"
        logger.info(f"Среда выполнения: {environment}")
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


# Функция при завершении работы бота
async def on_shutdown():
    try:
        logger.info("Закрытие соединения с базой данных...")
        await engine.dispose()
        logger.info("Соединение с базой данных закрыто")
    except Exception as e:
        logger.error(f"Ошибка при остановке: {e}")
    finally:
        logger.info("Бот остановлен")


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
        raise


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен вручную")
    except Exception as e:
        logger.critical(f"Необработанная ошибка: {e}")
        import traceback
        logger.critical(traceback.format_exc())
        sys.exit(1)