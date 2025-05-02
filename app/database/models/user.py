from sqlalchemy import Column, Integer, BigInteger, String, DateTime, JSON
from sqlalchemy.sql import func

from app.database.base import Base


class User(Base):
    """Модель пользователя в базе данных"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())

    # Информация о прохождении тестов
    # Сохраняем в формате JSON с информацией о каждой попытке:
    # [{"date": "2023-05-01T15:30:00", "score": 8, "answers": [0, 2, 1, ...]}]
    quiz_results = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, user_id={self.user_id}, username={self.username})>"