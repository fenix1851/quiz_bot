from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import CallbackQuery
from .config import Main, Admin, Client, Form
from keyboards.inline_buttoms import inline_kb_login
from .config import dp, bot
import psycopg2
from psycopg2 import Error

async def connect():
    """ Connect to the PostgreSQL database server """
    try:
        # Connect to an existing database read from .env file
        connection = psycopg2.connect(user = os.environ.get("POSTGRES_USER"),
                                        password = os.environ.get("POSTGRES_PASSWORD"),
                                        host = os.environ.get("POSTGRES_HOST"),
                                        port = os.environ.get("POSTGRES_PORT"),
                                        database = os.environ.get("POSTGRES_DB"))
        
        cursor = connection.cursor()
        # Print PostgreSQL Connection properties
        print ( connection.get_dsn_parameters(),"\n")

        # Print PostgreSQL version
        cursor.execute("SELECT version();")
        record = cursor.fetchone()
        print("You are connected to - ", record,"\n")
        return connection, cursor

    except (Exception, Error) as error :
        print ("Error while connecting to PostgreSQL", error)

@dp.message_handler(commands=['start', 'help'], state="*")
async def send_welcome(message: types.Message):
    stri = ""
    for i in message.text.split():
        stri += i + " "
    if len(message.text.split()) == 1:
        await Main.login.set()
        await message.reply("Привет выберите действие ", reply_markup=inline_kb_login)
    else:
        await Form.start.set()
        # Init inline keyboard with buttons "Начать опрос" and callback data message.text.split()[1]
        inline_kb_client = types.InlineKeyboardMarkup()
        form_id = message.text.split()[1].split("form_")[1]
        inline_kb_client.add(types.InlineKeyboardButton(text="Начать опрос", callback_data="form_"+form_id))
        await message.reply("Привет выберите действие " + form_id, reply_markup=inline_kb_client)

@dp.callback_query_handler(lambda c: c.data == "login_admin", state=["Main:login", "Main:start"])
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    admins = []
    # Get admins from database
    connection, cursor = await connect()
    cursor.execute("SELECT * FROM admin;")
    for row in cursor:
        admins.append(row[1])

    username = callback_query.from_user.username
    if username not in admins:
        await bot.send_message(callback_query.from_user.id, "Вы не являетесь администратором")
        return
    await Admin.start.set()
    await bot.send_message(callback_query.from_user.id, "Вы вошли как админ", reply_markup=inline_kb_admin)
