from typing import Dict, Any, Callable, Awaitable
from datetime import datetime
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: int = 1):
        # Простая реализация без внешних зависимостей
        self.cache = {}
        self.rate_limit = rate_limit
        
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Уникальный ключ для каждого пользователя и действия
        user_id = event.from_user.id if event.from_user else 0
        
        if isinstance(event, Message):
            key = f"{user_id}:{event.text or event.content_type}"
        else:
            key = f"{user_id}:callback:{event.data}"
        
        current_time = datetime.now()
        
        # Получаем время последнего запроса
        last_request_time = self.cache.get(key)
        
        # Если запрос был недавно, пропускаем
        if last_request_time and (current_time - last_request_time).total_seconds() < self.rate_limit:
            return None
            
        # Обновляем время последнего запроса
        self.cache[key] = current_time
        
        # Очищаем устаревшие записи
        keys_to_remove = []
        for k, v in self.cache.items():
            if (current_time - v).total_seconds() > 60:  # Удаляем записи старше 60 секунд
                keys_to_remove.append(k)
        
        for k in keys_to_remove:
            del self.cache[k]
            
        # Передаем управление дальше
        return await handler(event, data)