from aiogram.fsm.state import State, StatesGroup


class QuizStates(StatesGroup):
    """
    Состояния для машины состояний при прохождении теста
    """
    waiting_for_start = State()  # Ожидание начала теста
    answering = State()          # Процесс ответа на вопросы
    showing_results = State()    # Показ результатов