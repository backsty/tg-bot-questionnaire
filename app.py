# Для совместимости с Render, экспортируем WSGI app
from wsgi import app

# Также запускаем бот при прямом запуске этого модуля
if __name__ == "__main__":
    import os
    os.environ['BOT_ALREADY_RUNNING'] = 'True'
    from wsgi import run_bot
    run_bot()