import logging
import sys
import os
from dotenv import load_dotenv
import threading
import time
import asyncio
import json

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
    # Проверка на webhook-запрос от Telegram
    path = environ.get('PATH_INFO', '')
    bot_token = os.environ.get('BOT_TOKEN', '')
    
    # Обработка webhook-запросов от Telegram
    if path.startswith('/webhook/') and bot_token and path == f'/webhook/{bot_token}':
        # Чтение данных запроса
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            request_body_size = 0
            
        # Читаем данные запроса
        request_body = environ['wsgi.input'].read(request_body_size)
        update_data = json.loads(request_body) if request_body else {}
        
        logger.info(f"Получен webhook-запрос: {path[:30]}...")
        
        # Импортируем обработчик webhook из app
        try:
            from app.webhook_handler import handle_webhook
            result = handle_webhook(update_data)
            
            # Возвращаем ответ
            response_body = json.dumps(result).encode()
            status = '200 OK'
            headers = [('Content-Type', 'application/json'),
                      ('Content-Length', str(len(response_body)))]
            start_response(status, headers)
            return [response_body]
        except Exception as e:
            logger.error(f"Ошибка при обработке webhook: {e}")
            error_body = json.dumps({"ok": False, "error": str(e)}).encode()
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'application/json'),
                      ('Content-Length', str(len(error_body)))]
            start_response(status, headers)
            return [error_body]
    
    # Обычный ответ для других запросов
    status = '200 OK'
    headers = [('Content-type', 'text/plain')]
    start_response(status, headers)
    
    # Проверяем, работает ли бот
    bot_process = globals().get('bot_process')
    bot_status = "running" if bot_process and bot_process.is_alive() else "not running"
    
    # Вывод информации о состоянии и переменных окружения
    env_info = {
        "POSTGRES_HOST": os.environ.get("POSTGRES_HOST", "not set"),
        "POSTGRES_USER": os.environ.get("POSTGRES_USER", "not set"),
        "POSTGRES_DB": os.environ.get("POSTGRES_DB", "not set"),
        "POSTGRES_PORT": os.environ.get("POSTGRES_PORT", "not set"),
        "BOT_TOKEN": "present" if os.environ.get("BOT_TOKEN") else "not set",
        "WEBHOOK_URL": os.environ.get("WEBHOOK_URL", "not set")
    }
    
    logger.info(f"Bot status: {bot_status}")
    logger.info(f"Environment: {json.dumps(env_info)}")
    
    # Если бот не запущен, запускаем его
    if bot_status == "not running" and not os.environ.get('BOT_ALREADY_RUNNING'):
        start_bot()
        bot_status = "starting"
    
    return [f"Telegram bot is {bot_status}".encode()]


# Используем webhooks вместо поллинга
def run_bot():
    try:
        logger.info("Запуск бота...")
        
        # Импортируем необходимые модули
        from app.config import BOT_TOKEN, PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DB
        
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN не установлен. Невозможно запустить бота.")
            return
        
        # Выводим информацию о базе данных без пароля
        logger.info(f"База данных: {PG_USER}@{PG_HOST}:{PG_PORT}/{PG_DB}")
        
        # Используем простой HTTP-запрос для настройки бота без поллинга
        import requests
        
        # Устанавливаем команды бота через API
        commands = [
            {"command": "start", "description": "Запустить бота"},
            {"command": "help", "description": "Помощь по использованию"},
            {"command": "quiz", "description": "Начать тест"}
        ]
        
        try:
            # Настраиваем команды бота через API
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands",
                json={"commands": commands}
            )
            if response.status_code == 200:
                logger.info("Команды бота успешно настроены")
            else:
                logger.error(f"Ошибка при настройке команд: {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при настройке команд: {e}")
        
        # Отправляем сообщение администратору о том, что бот запущен
        admin_id = os.environ.get("ADMIN_ID")
        if admin_id:
            try:
                requests.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    params={
                        "chat_id": admin_id,
                        "text": f"🤖 Бот запущен!\nБаза данных: {PG_HOST}/{PG_DB}"
                    }
                )
                logger.info("Уведомление администратора отправлено")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления: {e}")
        
        # Получаем информацию о боте
        try:
            response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
            if response.status_code == 200:
                bot_info = response.json()["result"]
                logger.info(f"Бот @{bot_info['username']} ({bot_info['first_name']}) запущен")
            else:
                logger.error(f"Ошибка при получении информации о боте: {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при получении информации о боте: {e}")
        
        # Настроим webhook для получения обновлений
        # На Render у вас есть внешний URL для вашего сервиса
        webhook_url = os.environ.get("WEBHOOK_URL")
        if webhook_url:
            try:
                # Удаляем предыдущие webhook-и
                reset_response = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
                )
                logger.info(f"Сброс webhook: {reset_response.status_code}")
                
                # Устанавливаем новый webhook
                webhook_path = f"{webhook_url}/webhook/{BOT_TOKEN}"
                response = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
                    json={"url": webhook_path}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        logger.info(f"Webhook успешно настроен: {webhook_path[:30]}...")
                    else:
                        logger.error(f"Ошибка при установке webhook: {result}")
                else:
                    logger.error(f"Ошибка при настройке webhook: {response.text}")
                    
                # Проверяем настройку webhook
                info_response = requests.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
                )
                if info_response.status_code == 200:
                    logger.info(f"Webhook info: {info_response.json()}")
            except Exception as e:
                logger.error(f"Ошибка при настройке webhook: {e}")
        else:
            logger.warning("WEBHOOK_URL не установлен. Бот не сможет получать обновления через webhook.")
        
        # Бот считается запущенным
        logger.info("Бот успешно запущен")
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())


# Функция для запуска бота в отдельном потоке
def start_bot():
    if not os.environ.get('BOT_ALREADY_RUNNING'):
        os.environ['BOT_ALREADY_RUNNING'] = 'True'
        logger.info("Запуск потока с ботом")
        
        # Запускаем простую инициализацию в отдельном потоке
        thread = threading.Thread(target=run_bot, daemon=True)
        thread.start()
        globals()['bot_process'] = thread
        logger.info("Поток для бота запущен")
        return thread
    else:
        logger.info("Бот уже запущен")
        return None


# Инициализация при импорте модуля
if not os.environ.get('BOT_ALREADY_RUNNING'):
    # Начнем с некоторой задержкой, чтобы дать Gunicorn возможность инициализироваться
    def delayed_start():
        logger.info("Ожидание 10 секунд перед запуском бота...")
        time.sleep(10)
        bot_process = start_bot()
        logger.info("Инициализация бота завершена")

    startup_thread = threading.Thread(target=delayed_start, daemon=True)
    startup_thread.start()