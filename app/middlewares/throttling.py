from typing import Dict, Any, Callable, Awaitable
from datetime import datetime

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class ThrottlingMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты запросов к боту
    """

    def __init__(self, limit=0.5):
        self.rate_limit = limit
        self.cache = {}

    async def __call__(
            self,
            handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        """
        Проверяет запросы на превышение лимита
        """
        user_id = event.from_user.id

        # Если пользователь уже в кэше и время не истекло
        current_time = datetime.now().timestamp()
        if user_id in self.cache:
            last_request_time = self.cache[user_id]
            time_passed = current_time - last_request_time

            if time_passed < self.rate_limit:
                if isinstance(event, CallbackQuery):
                    await event.answer("Слишком много запросов! Пожалуйста, подождите.", show_alert=True)
                elif isinstance(event, Message):
                    await event.answer("Слишком много запросов! Пожалуйста, подождите.")
                return None

        self.cache[user_id] = current_time
        return await handler(event, data)