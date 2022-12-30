from aiogram.dispatcher.filters.state import State, StatesGroup

class Client(StatesGroup):
    start = State()
    form = State()
    form_info = State()