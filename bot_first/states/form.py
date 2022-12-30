from aiogram.dispatcher.filters.state import State, StatesGroup

class Form(StatesGroup):
    start = State()
    form_info = State()
    form_end = State()
    form_input = State()