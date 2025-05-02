import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BinaryExpression

from app.database.models.user import User
from app.utils.quiz_data import QUIZ_DATA, get_grade


class QuizService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: int) -> Optional[User]:
        """
        Получает пользователя из БД или создает нового
        """
        condition = cast(BinaryExpression, User.user_id == user_id)
        stmt = select(User).where(condition)
        result = await self.session.execute(stmt)
        user = result.scalars().first()

        if not user:
            user = User(user_id=user_id)
            self.session.add(user)
            await self.session.commit()

        return user

    async def update_user_info(self, user_id: int, **kwargs):
        """
        Обновляет информацию о пользователе
        """
        user = await self.get_user(user_id)

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        # Явный коммит изменений
        await self.session.commit()
        return user

    async def save_quiz_result(self, user_id: int, score: int, answers: List[int]):
        """
        Сохраняет результат прохождения теста
        """
        user = await self.get_user(user_id)

        # Создаем запись о результате теста
        result = {
            "date": datetime.now().isoformat(),
            "score": score,
            "answers": answers
        }

        # Добавляем к существующим результатам или создаем новый список
        if user.quiz_results:
            results = json.loads(user.quiz_results)
            results.append(result)
            user.quiz_results = json.dumps(results)
        else:
            user.quiz_results = json.dumps([result])

        # Сохраняем изменения
        await self.session.commit()
        return user

    async def get_user_results(self, user_id: int) -> List[Dict]:
        """
        Получает историю прохождения тестов пользователя
        """
        user = await self.get_user(user_id)

        if not user.quiz_results:
            return []

        return json.loads(user.quiz_results)

    @staticmethod
    def check_answer(question_id: int, answer_id: int) -> bool:
        """
        Проверяет, верный ли ответ дал пользователь
        """
        if 0 <= question_id < len(QUIZ_DATA):
            return QUIZ_DATA[question_id]["correct"] == answer_id
        return False

    @staticmethod
    def calculate_score(answers: List[int]) -> Tuple[int, str, str]:
        """
        Вычисляет итоговый балл за тест и возвращает оценку
        """
        score = sum(1 for q_id, a_id in enumerate(answers)
                    if q_id < len(QUIZ_DATA) and a_id == QUIZ_DATA[q_id]["correct"])
        grade, comment = get_grade(score)
        return score, grade, comment