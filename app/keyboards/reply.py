from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_keyboard():
    """
    Основная клавиатура для взаимодействия с ботом
    """
    builder = ReplyKeyboardBuilder()

    # Добавляем кнопки
    builder.add(
        KeyboardButton(text="🚀 Начать тест"),
        KeyboardButton(text="📊 Мои результаты"),
        KeyboardButton(text="📚 О тесте"),
        KeyboardButton(text="❓ Помощь")
    )

    # Располагаем кнопки 2 в ряду
    builder.adjust(2)

    return builder.as_markup(resize_keyboard=True)