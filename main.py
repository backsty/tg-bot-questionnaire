import asyncio
import logging
from aiogram.types import BotCommand

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

# Регистрация обработчиков
register_common_handlers(dp)
register_quiz_handlers(dp)


# Функция создания таблиц базы данных при запуске
async def on_startup():
    logging.info("Создание таблиц в базе данных...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Таблицы базы данных созданы")

    # Устанавливаем команды бота
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Помощь по использованию"),
        BotCommand(command="quiz", description="Начать тест")
    ])

    logging.info("Бот запущен")


# Функция при завершении работы бота
async def on_shutdown():
    logging.info("Закрытие соединения с базой данных...")
    await engine.dispose()
    logging.info("Соединение с базой данных закрыто")
    logging.info("Бот остановлен")


async def main():
    # Устанавливаем обработчики запуска и остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Запускаем бота
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")