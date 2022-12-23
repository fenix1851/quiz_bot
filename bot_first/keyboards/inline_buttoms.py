# Add inline keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Create inline keyboard
inline_kb_login = InlineKeyboardMarkup(row_width=2)
# Add callback data to buttons
inline_kb_login.add(InlineKeyboardButton("Войти как админ", callback_data="login_admin"))
# inline_kb_login.add(InlineKeyboardButton("Войти как клиент", callback_data="login_client"))

# Create admin inline keyboard
inline_kb_admin = InlineKeyboardMarkup(row_width=2)
# Add callback data to buttons
inline_kb_admin.add(InlineKeyboardButton("Создать форму", callback_data="create_form"))
inline_kb_admin.add(InlineKeyboardButton("Просмотреть все формы", callback_data="forms_all"))
inline_kb_admin.add(InlineKeyboardButton("Залить фотографии", callback_data="upload_photo"))
inline_kb_admin.add(InlineKeyboardButton("Администраторы", callback_data="admins"))
inline_kb_admin.add(InlineKeyboardButton("Промокод", callback_data="promo"))
inline_kb_admin.add(InlineKeyboardButton("Выйти", callback_data="exit"))
