import asyncio
import logging
import os
import threading
import signal
import queue
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

# Очередь сообщений для взаимодействия между потоками
message_queue = queue.Queue()
bot_running = True


# Функция удаления webhook перед запуском
async def remove_webhook():
    """Удаляет webhook перед запуском поллинга и сбрасывает обновления"""
    logger.info("Проверка и удаление webhook...")
    try:
        # Пауза перед проверкой webhook, чтобы избежать конфликтов с предыдущими экземплярами
        await asyncio.sleep(5)  # Увеличиваем задержку до 5 секунд
        
        # Повторяем попытки удаления webhook при конфликтах
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                webhook_info = await bot.get_webhook_info()
                if webhook_info.url:
                    logger.info(f"Найден активный webhook: {webhook_info.url}")
                    # Удаляем webhook с удалением всех ожидающих обновлений
                    await bot.delete_webhook(drop_pending_updates=True)
                    logger.info("Webhook удален и ожидающие обновления сброшены")
                else:
                    logger.info("Webhook не настроен")
                
                # Сбрасываем все ожидающие обновления для избежания конфликтов
                await bot.get_updates(offset=-1, limit=1)
                logger.info("Ожидающие обновления сброшены, запуск в режиме поллинга")
                
                # Если дошли сюда без исключений, выходим из цикла
                break
            except Exception as e:
                logger.warning(f"Попытка {attempt}/{max_attempts}: Ошибка при удалении webhook: {e}")
                await asyncio.sleep(3)  # Ждем перед повторной попыткой
                
                # Если это была последняя попытка и все равно есть ошибка
                if attempt == max_attempts:
                    logger.error("Исчерпаны все попытки удаления webhook")
                    raise  # Пробрасываем исключение выше
    except Exception as e:
        logger.error(f"Критическая ошибка при удалении webhook: {e}")
        import traceback
        logger.error(traceback.format_exc())


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
    
    logger.info(f"Бот запущен в режиме поллинга")


# Функция при завершении работы бота
async def on_shutdown():
    logger.info("Закрытие соединения с базой данных...")
    await engine.dispose()
    logger.info("Соединение с базой данных закрыто")
    logger.info("Бот остановлен")


async def start_polling():
    """Запуск бота в режиме поллинга без обработки сигналов"""
    from aiogram.types import BotCommand
    
    # Регистрация обработчиков
    register_common_handlers(dp)
    register_quiz_handlers(dp)
    
    # Запускаем стартовую функцию вручную, вместо регистрации
    await on_startup()
    
    # Добавляем глобальный обработчик для автоматического перезапуска при конфликте
    conflict_count = 0
    max_conflicts = 5
    
    try:
        while True:  # Цикл для автоматического перезапуска при конфликтах
            try:
                # Получаем последний update_id и используем его как offset для сброса всех предыдущих обновлений
                updates = await bot.get_updates(offset=-1, limit=1)
                offset = updates[-1].update_id + 1 if updates else None
                logger.info(f"Начинаем поллинг с offset={offset}")
                
                # Используем явный offset при запуске поллинга с ограниченным временем
                await dp.start_polling(
                    bot, 
                    handle_signals=False,
                    polling_timeout=10,
                    reset_webhook=False, 
                    skip_updates=True, 
                    offset=offset,
                    timeout=30  # Добавляем таймаут для всех операций
                )
                
                # Если мы дошли до этой точки без исключений, сбрасываем счетчик конфликтов
                conflict_count = 0
                
            except Exception as e:
                if "Conflict: terminated by other getUpdates request" in str(e):
                    conflict_count += 1
                    logger.warning(f"Конфликт с другой инстанцией бота ({conflict_count}/{max_conflicts})")
                    
                    if conflict_count >= max_conflicts:
                        logger.error("Слишком много конфликтов, останавливаем бота")
                        break
                        
                    # Ждем перед повторной попыткой, увеличивая время ожидания с каждой попыткой
                    wait_time = 5 * conflict_count  # 5, 10, 15, 20, 25 секунд
                    logger.info(f"Ожидание {wait_time} секунд перед повторной попыткой...")
                    await asyncio.sleep(wait_time)
                    
                    # Сбрасываем webhook и обновления перед новой попыткой
                    await remove_webhook()
                    continue
                    
                else:
                    # Для других исключений логируем и выходим
                    logger.error(f"Ошибка в процессе поллинга: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    break
                    
    except Exception as e:
        logger.error(f"Глобальная ошибка в процессе поллинга: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Выполняем shutdown вручную
        await on_shutdown()


def run_bot():
    """Запуск бота в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    global bot_running
    
    try:
        loop.run_until_complete(start_polling())
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        bot_running = False
        loop.close()


async def health_check(request):
    """Эндпоинт для проверки работоспособности сервиса"""
    if bot_running:
        return web.Response(text="Telegram bot is running!")
    else:
        return web.Response(text="Bot is not running", status=500)


async def on_startup_app(app):
    """Функция, которая выполняется при запуске веб-сервера"""
    logger.info(f"Веб-сервер запущен на порту {PORT}")


def main():
    """Основная функция для запуска веб-сервера и бота"""
    # Обработчик сигналов устанавливаем только в основном потоке
    def signal_handler(sig, frame):
        global bot_running
        logger.info("Получен сигнал завершения, останавливаем сервис...")
        bot_running = False
        # Поместить сообщение в очередь для остановки бота
        message_queue.put("STOP")
    
    # Устанавливаем обработчики сигналов только в основном потоке
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    from keepalive import start_monitoring
    start_monitoring()  # Запускаем мониторинг бота в отдельном потоке
    logger.info("Мониторинг бота запущен")
    
    # Запускаем бот в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("Бот запущен в отдельном потоке")
    
    # Создаем веб-приложение
    app = web.Application()
    
    # Добавляем маршруты
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    # Запускаем веб-сервер
    app.on_startup.append(on_startup_app)
    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    from aiogram.types import BotCommand
    main()