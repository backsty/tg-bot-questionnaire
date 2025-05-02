from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.emoji import ROCKET, BRAIN, CHART, BOOK


def get_start_keyboard():
    """
    Клавиатура для начального меню
    """
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text=f"{ROCKET} Начать тест", callback_data="start_quiz"))
    builder.add(InlineKeyboardButton(text=f"{BRAIN} О тесте", callback_data="about_quiz"))
    builder.add(InlineKeyboardButton(text=f"{CHART} Мои результаты", callback_data="my_results"))
    builder.add(InlineKeyboardButton(text=f"{BOOK} Помощь", callback_data="help"))

    # Устанавливаем по одной кнопке в ряду
    builder.adjust(1)

    return builder.as_markup()


def get_quiz_options(question_id: int, options: list):
    """
    Клавиатура с вариантами ответов для вопроса
    """
    builder = InlineKeyboardBuilder()

    for i, option in enumerate(options):
        # Создаем callback_data в формате answer:номер_вопроса:номер_ответа
        callback_data = f"answer:{question_id}:{i}"
        # Добавляем буквенные обозначения к вариантам ответа
        button_text = f"{chr(97 + i)}) {option}"
        builder.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    # Устанавливаем по одной кнопке в ряду
    builder.adjust(1)

    return builder.as_markup()


def get_continue_keyboard():
    """
    Клавиатура для продолжения после завершения теста
    """
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="Пройти тест снова", callback_data="start_quiz"),
        InlineKeyboardButton(text="В главное меню", callback_data="back_to_menu")
    )

    # Устанавливаем по одной кнопке в ряду
    builder.adjust(1)

    return builder.as_markup()