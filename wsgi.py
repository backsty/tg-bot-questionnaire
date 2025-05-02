import asyncio
import threading
import time
import os
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла, если он есть
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def app(environ, start_response):
    """Простой WSGI-интерфейс для Gunicorn"""
    status = '200 OK'
    headers = [('Content-type', 'text/plain')]
    start_response(status, headers)
    
    # Проверяем, запущен ли бот
    bot_status = "running" if os.environ.get('BOT_ALREADY_RUNNING') else "not running"
    return [f"Telegram bot is {bot_status}".encode()]


# Функция для запуска бота в отдельном потоке
def run_bot():
    try:
        logger.info("Запуск бота в отдельном потоке")
        # Импортируем main только здесь, чтобы избежать циклического импорта
        from main import main
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Проверяем наличие необходимых переменных окружения
        required_vars = ['BOT_TOKEN', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
        for var in required_vars:
            if not os.environ.get(var):
                logger.error(f"Отсутствует переменная окружения {var}")
                return
                
        loop.run_until_complete(main())
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        # Делаем трассировку исключения доступной в логах
        import traceback
        logger.error(traceback.format_exc())


# Запускаем бота в отдельном потоке только если файл запущен как модуль
if not os.environ.get('BOT_ALREADY_RUNNING'):
    os.environ['BOT_ALREADY_RUNNING'] = 'True'
    logger.info("Запуск потока с ботом")
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    # Даем боту время на запуск
    time.sleep(5)
    logger.info("Бот запущен в отдельном потоке")
else:
    logger.info("Бот уже запущен в другом потоке")