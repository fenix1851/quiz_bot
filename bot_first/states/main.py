from aiogram.dispatcher.filters.state import State, StatesGroup

class Main(StatesGroup):
    start = State()
    login = State()