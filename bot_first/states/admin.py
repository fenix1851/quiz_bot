from aiogram.dispatcher.filters.state import State, StatesGroup

class Admin(StatesGroup):
    start = State()
    form = State()
    forms_all = State()
    new_form = State()
    form_info = State()
    upload_photo = State()
    admins = State()
    add_admin = State()
    delete_admin = State()
    promo = State()
    promo_choose = State()
    promo_delete = State()