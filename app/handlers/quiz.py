from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.states.quiz import QuizStates
from app.keyboards.inline import get_quiz_options, get_continue_keyboard, get_start_keyboard
from app.services.quiz_service import QuizService
from app.database.engine import get_session
from app.utils.quiz_data import QUIZ_DATA
from app.utils.emoji import BRAIN, CHECK, CROSS, TROPHY, STAR, BOOK, ROCKET, ROBOT


async def cmd_quiz(message: Message, state: FSMContext):
    """
    Запускает тест по информатике
    """
    # Инициализируем состояние теста с начальными данными
    await state.clear()
    await state.update_data(
        current_question=0,  # Текущий вопрос
        answers=[],  # Ответы пользователя
        score=0  # Количество правильных ответов
    )

    # Переходим в состояние ответа на вопросы
    await state.set_state(QuizStates.answering)

    # Показываем первый вопрос
    await show_question(message, state)


async def show_question(message_or_query, state: FSMContext, show_result=False):
    """
    Показывает текущий вопрос теста
    """
    data = await state.get_data()
    question_id = data['current_question']

    # Проверяем, показывать ли результат предыдущего вопроса
    text = ""
    if show_result and question_id > 0:
        # Получаем данные о предыдущем ответе
        answers = data['answers']
        prev_answer = answers[-1]
        prev_question = question_id - 1
        prev_question_text = QUIZ_DATA[prev_question]['question']
        correct_option = QUIZ_DATA[prev_question]['correct']
        options = QUIZ_DATA[prev_question]['options']

        if prev_answer == correct_option:
            text += f"{CHECK} <b>Правильно!</b>\n"
            text += f"Вопрос: {prev_question_text}\n"
            text += f"Ответ: {options[correct_option]}\n\n"
        else:
            text += f"{CROSS} <b>Неправильно.</b>\n"
            text += f"Вопрос: {prev_question_text}\n"
            text += f"Ваш ответ: {options[prev_answer]}\n"
            text += f"Правильный ответ: {options[correct_option]}\n\n"

    # Проверяем, остались ли еще вопросы или нужно показать результат
    if question_id >= len(QUIZ_DATA):
        await show_results(message_or_query, state)
        return

    # Получаем текущий вопрос и варианты ответов
    question = QUIZ_DATA[question_id]
    text += f"{BRAIN} <b>Вопрос {question_id + 1}/{len(QUIZ_DATA)}</b>\n\n"
    text += f"{question['question']}"

    # Создаем клавиатуру с вариантами ответов
    keyboard = get_quiz_options(question_id, question['options'])

    # Отправляем сообщение в зависимости от типа входящего объекта
    if isinstance(message_or_query, Message):
        await message_or_query.answer(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message_or_query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


async def process_answer(query: CallbackQuery, state: FSMContext):
    """
    Обрабатывает ответ пользователя на вопрос
    """
    await query.answer()  # Сбрасываем состояние ожидания у кнопки

    # Разбираем callback_data
    _, question_id, answer_id = query.data.split(":")
    question_id, answer_id = int(question_id), int(answer_id)

    # Получаем текущее состояние
    data = await state.get_data()
    current_question = data['current_question']

    # Проверяем, что ответ на текущий вопрос
    if question_id != current_question:
        return

    # Проверяем правильность ответа
    is_correct = QuizService.check_answer(question_id, answer_id)

    # Обновляем данные в состоянии
    answers = data.get('answers', [])
    answers.append(answer_id)
    score = data.get('score', 0)

    if is_correct:
        score += 1

    await state.update_data(
        current_question=current_question + 1,
        answers=answers,
        score=score
    )

    # Показываем следующий вопрос с результатом предыдущего
    await show_question(query, state, show_result=True)


async def show_results(message_or_query, state: FSMContext):
    """
    Показывает результаты теста
    """
    # Получаем данные из состояния
    data = await state.get_data()
    answers = data['answers']

    # Получаем оценку на основе набранных баллов
    # Обратите внимание: мы не используем score из state, а рассчитываем заново
    score, grade, comment = QuizService.calculate_score(answers)

    # Формируем текст с результатами
    text = f"{TROPHY} <b>Тест завершен!</b>\n\n"
    text += f"Вы ответили правильно на <b>{score}/{len(QUIZ_DATA)}</b> вопросов.\n\n"
    text += f"Ваша оценка: <b>{grade}</b>\n"
    text += f"{comment}\n\n"

    # Добавляем эмоджи к результату
    if score >= 9:
        text += f"{TROPHY} Отлично! Вы настоящий эксперт в информатике!"
    elif score >= 7:
        text += f"{STAR} Хороший результат! Продолжайте в том же духе!"
    elif score >= 5:
        text += f"{CHECK} Неплохо, но есть куда расти. Повторите некоторые темы."
    else:
        text += f"{BOOK} Рекомендуем еще раз изучить основы информатики."

    # Создаем клавиатуру с действиями после завершения теста
    keyboard = get_continue_keyboard()

    # Сохраняем результат в базу данных
    user_id = message_or_query.from_user.id if isinstance(message_or_query, Message) else message_or_query.from_user.id

    async for session in get_session():
        service = QuizService(session)
        await service.save_quiz_result(user_id, score, answers)

    # Сбрасываем состояние
    await state.clear()

    # Отправляем результаты
    if isinstance(message_or_query, Message):
        await message_or_query.answer(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message_or_query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


async def view_results(message: Message):
    """
    Показывает историю результатов пользователя
    """
    async for session in get_session():
        service = QuizService(session)
        results = await service.get_user_results(message.from_user.id)

        if not results:
            await message.answer(
                f"{BOOK} У вас пока нет завершенных тестов. Нажмите '{ROCKET} Начать тест', чтобы пройти тест.",
                parse_mode="HTML",
                reply_markup=get_start_keyboard()
            )
            return

        text = f"{TROPHY} <b>Ваши результаты:</b>\n\n"

        for i, result in enumerate(results[-5:], 1):  # Показываем последние 5 результатов
            date = result["date"].split("T")[0]  # Упрощенный формат даты
            score = result["score"]
            text += f"{i}. <b>{date}</b>: {score}/{len(QUIZ_DATA)} правильных ответов\n"

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_start_keyboard()
        )


async def menu_callbacks(query: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатия на кнопки в главном меню
    """
    await query.answer()

    if query.data == "start_quiz":
        # Запускаем тест
        await cmd_quiz(query.message, state)

    elif query.data == "about_quiz":
        # Показываем информацию о тесте
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

        await query.message.edit_text(
            about_text,
            parse_mode="HTML",
            reply_markup=get_start_keyboard()
        )

    elif query.data == "my_results":
        # Показываем результаты пользователя
        async for session in get_session():
            service = QuizService(session)
            results = await service.get_user_results(query.from_user.id)

            if not results:
                await query.message.edit_text(
                    f"{BOOK} У вас пока нет завершенных тестов. Нажмите '{ROCKET} Начать тест', чтобы пройти тест.",
                    parse_mode="HTML",
                    reply_markup=get_start_keyboard()
                )
                return

            text = f"{TROPHY} <b>Ваши результаты:</b>\n\n"

            for i, result in enumerate(results[-5:], 1):  # Показываем последние 5 результатов
                date = result["date"].split("T")[0]  # Упрощенный формат даты
                score = result["score"]
                text += f"{i}. <b>{date}</b>: {score}/{len(QUIZ_DATA)} правильных ответов\n"

            await query.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=get_start_keyboard()
            )

    elif query.data == "help":
        # Показываем справку
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

        await query.message.edit_text(
            help_text,
            parse_mode="HTML",
            reply_markup=get_start_keyboard()
        )

    elif query.data == "back_to_menu":
        # Возвращаемся в главное меню
        # Формируем приветственное сообщение
        greeting_text = (
            f"{ROBOT} <b>Вы вернулись в главное меню</b>\n\n"
            f"{BRAIN} Я бот для прохождения теста по информатике для 10 класса.\n\n"
            f"{BOOK} Тема: <b>Основы информатики и программирования</b>\n\n"
            f"Выбери действие в меню ниже:"
        )

        # Отправляем приветственное сообщение с инлайн-клавиатурой
        await query.message.edit_text(
            greeting_text,
            parse_mode="HTML",
            reply_markup=get_start_keyboard()
        )


def register_quiz_handlers(dp):
    """
    Регистрирует обработчики для работы с тестом
    """
    # Создаем роутер для обработчиков викторины
    router = Router()

    # Регистрируем обработчики сообщений
    router.message.register(cmd_quiz, Command(commands=["quiz"]))
    router.message.register(cmd_quiz, F.text.in_(["🚀 Начать тест", "Начать тест"]))
    router.message.register(view_results, F.text.in_(["📊 Мои результаты", "Мои результаты"]))

    # Регистрируем обработчики callback-запросов
    router.callback_query.register(
        menu_callbacks,
        F.data.in_(["start_quiz", "about_quiz", "my_results", "help", "back_to_menu"])
    )

    # Регистрируем обработчик ответов на вопросы
    router.callback_query.register(
        process_answer,
        F.data.startswith("answer:"),
        QuizStates.answering
    )

    # Включаем роутер в диспетчер
    dp.include_router(router)