import threading
import time
import logging
import os
import requests
import subprocess

logger = logging.getLogger(__name__)

def check_bot_status():
    """
    Периодически проверяет состояние бота и перезапускает его при необходимости
    """
    interval = 30  # Проверка каждые 30 секунд
    
    while True:
        try:
            # Проверяем локальный health-endpoint
            response = requests.get("http://localhost:10000/health", timeout=5)
            
            if response.status_code != 200:
                logger.error(f"Бот не отвечает! Статус: {response.status_code}")
                restart_bot()
        except Exception as e:
            logger.error(f"Ошибка при проверке состояния бота: {e}")
        
        time.sleep(interval)

def restart_bot():
    """
    Перезапускает бота в новом процессе
    """
    try:
        logger.warning("Перезапуск бота...")
        # Здесь мы перезапускаем текущий процесс
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        logger.error(f"Ошибка при перезапуске бота: {e}")

def start_monitoring():
    """
    Запускает мониторинг в отдельном потоке
    """
    monitor_thread = threading.Thread(target=check_bot_status, daemon=True)
    monitor_thread.start()
    logger.info("Мониторинг бота запущен")