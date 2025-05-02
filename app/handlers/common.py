from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from app.keyboards.inline import get_start_keyboard
from app.keyboards.reply import get_main_keyboard
from app.services.quiz_service import QuizService
from app.database.engine import get_session
from app.utils.emoji import ROBOT, BRAIN, BOOK, COMPUTER


async def cmd_start(message: Message, state: FSMContext):
    """
    Обрабатывает команду /start - показывает приветственное сообщение
    """
    # Очищаем предыдущее состояние
    await state.clear()

    try:
        # Получаем сессию БД и работаем с ней внутри контекста
        async for session in get_session():
            service = QuizService(session)

            # Сохраняем информацию о пользователе
            await service.update_user_info(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
    except Exception as e:
        logging.error(f"Ошибка при работе с БД: {e}")

    # Формируем приветственное сообщение
    greeting_text = (
        f"{ROBOT} <b>Привет, {message.from_user.first_name}!</b>\n\n"
        f"{BRAIN} Я бот для прохождения теста по информатике для 10 класса.\n\n"
        f"{BOOK} Тема: <b>Основы информатики и программирования</b>\n\n"
        f"{COMPUTER} В тесте 10 вопросов с выбором варианта ответа.\n"
        f"После завершения теста ты получишь свою оценку и рекомендации.\n\n"
        f"Выбери действие в меню ниже:"
    )

    # Отправляем приветственное сообщение с инлайн-клавиатурой
    await message.answer(
        greeting_text,
        parse_mode="HTML",
        reply_markup=get_start_keyboard()
    )

    # Устанавливаем основную клавиатуру
    await message.answer(
        "Используй кнопки для навигации:",
        reply_markup=get_main_keyboard()
    )


async def cmd_help(message: Message):
    """
    Обрабатывает команду /help - показывает информацию о боте
    """
    help_text = (
        f"{BOOK} <b>Справка по боту:</b>\n\n"
        f"• Нажми «Начать тест» для прохождения теста по информатике\n"
        f"• В тесте 10 вопросов с вариантами ответов\n"
        f"• После прохождения теста ты получишь оценку и рекомендации\n"
        f"• В разделе «Мои результаты» можно посмотреть историю прохождения\n\n"
        f"Команды бота:\n"
        f"/start - начать взаимодействие с ботом\n"
        f"/help - показать эту справку\n"
        f"/quiz - начать тестирование\n"
    )

    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


async def about_quiz(message: Message):
    """
    Показывает информацию о тесте
    """
    about_text = (
        f"{BRAIN} <b>О тесте по информатике:</b>\n\n"
        f"• Тест предназначен для учащихся 10 класса\n"
        f"• Тема: «Основы информатики и программирования»\n"
        f"• Включает вопросы о базовых понятиях и терминах информатики\n"
        f"• Затрагивает темы о компьютерной архитектуре и языках программирования\n\n"
        f"<b>Критерии оценки:</b>\n"
        f"• 9–10 правильных ответов — отлично! 🏆\n"
        f"• 7–8 — хорошо ⭐\n"
        f"• 5–6 — удовлетворительно ✅\n"
        f"• Меньше 5 — стоит повторить материал 📚"
    )

    await message.answer(
        about_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


def register_common_handlers(dp):
    """
    Регистрирует обработчики общих команд
    """
    # Создаем роутер для общих команд
    router = Router()

    # Регистрируем хендлеры на роутере
    router.message.register(cmd_start, CommandStart())
    router.message.register(cmd_help, Command(commands=["help"]))
    router.message.register(about_quiz, F.text.in_(["📚 О тесте", "О тесте"]))
    router.message.register(cmd_help, F.text.in_(["❓ Помощь", "Помощь"]))

    # Включаем роутер в диспетчер
    dp.include_router(router)