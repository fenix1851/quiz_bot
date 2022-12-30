import csv
import logging
import os

from aiogram import Bot, Dispatcher, executor, types
# Add states
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from keyboards.inline_buttoms import inline_kb_login, inline_kb_admin
from dotenv import load_dotenv
from openpyxl import Workbook
import qrcode
import random
from states.main import Main
from states.form import Form
from states.admin import Admin
from states.client import Client

load_dotenv()

# Connect to postgresql database
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

# Configure bot

storage = MemoryStorage()

API_TOKEN = os.environ.get("API_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

# Simple bot command
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

# STart form with questions from csv file with name message.text.split()[1]
@dp.callback_query_handler(lambda c: c.data.split("_")[0] == "form", state="Form:start")
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    # Read from cvs file and create a list of values
    # Get from file_id from callback data and fined in database
    connection, cursor = await connect()
    cursor.execute("SELECT * FROM forms WHERE id = %s", (callback_query.data.split("_")[1],))
    record = cursor.fetchone()
    with open(record[1], 'r') as f:
        reader = csv.reader(f)
        data = list(reader)
    i = 1
    await state.update_data(i=i)
    await state.update_data(record=record[1])
    print(data)
    inline_kb_form = types.InlineKeyboardMarkup()
    inline_kb_form.add(types.InlineKeyboardButton(text="Начать", callback_data="active_"))
    await bot.send_message(callback_query.from_user.id, data[0][3], reply_markup=inline_kb_form)

# Start form with questions from csv file with name message.text.split()[1]
@dp.callback_query_handler(lambda c: c.data.split("_")[0] == "active", state="Form:start")
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    # Write to state data from callback query
    print(callback_query.data)
    record = await state.get_data()
    record = record["record"]
    with open(record, 'r') as f:
        reader = csv.reader(f)
        data = list(reader)
    n = len(data[1])
    i = await state.get_data()
    i = i["i"]
    await state.update_data(i=i+1)
    print(i)
    if i == 1:
        await state.update_data(answers=[])
    else:
        # get data from state and uppend to list
        datas = await state.get_data()
        # Get answers from state and read from csv file
        answ = callback_query.data.split("_")[1]
        # Get from data list of answers an dget answ with index answer
        arr = []
        print(answ)
        for j in answ.split(","):
            arr.append(data[3][i-1].split(",")[int(j)-1])
        datas["answers"].append(arr)
        await state.update_data(answers=datas["answers"])
    inline_kb_form = types.InlineKeyboardMarkup()  
    if i > n-1:
        inline_kb_form.add(types.InlineKeyboardButton(text="Завершить", callback_data="endForm_"))
        await bot.send_message(callback_query.from_user.id, "Нажмите на кнопку Завершить чтобы отправить ответы", reply_markup=inline_kb_form)
        # Set state to end form
        await Form.form_end.set()
        return
    if data[2][i] == "Одиночный выбор":
        for k,j in enumerate(data[3][i].split(",")):
            text = str(j.strip())
            call_back = "active_"+ str(k)
            inline_kb_form.add(types.InlineKeyboardButton(text=text, callback_data=call_back))
    else:
        await Form.form_input.set()
        # inline_kb_form.add(types.InlineKeyboardButton(text=data[3][i], callback_data="active_"))
    if data[4][i] != "":
        await bot.send_photo(callback_query.from_user.id, data[4][i])
    await bot.send_message(callback_query.from_user.id, data[1][i], reply_markup=inline_kb_form)

# process if user write answer to question 
@dp.message_handler(state="Form:form_input")
async def process_callback_button1(message: types.Message, state: FSMContext):
    answ = message.text
    datas = await state.get_data()
    datas["answers"].append(answ)
    await state.update_data(answers=datas["answers"])
    i = await state.get_data()
    i = i["i"]
    print(i)
    await state.update_data(i=datas["i"]+1)
    inline_kb_form = types.InlineKeyboardMarkup()  
    record = await state.get_data()
    record = record["record"]
    with open(record, 'r') as f:
        reader = csv.reader(f)
        data = list(reader)
    n = len(data[1])
    if i > n-1:
        inline_kb_form.add(types.InlineKeyboardButton(text="Завершить", callback_data="endForm_"))
        await bot.send_message(message.from_user.id, "Нажмите на кнопку Завершить чтобы отправить ответы", reply_markup=inline_kb_form)
        # Set state to end form
        await Form.form_end.set()
        return
    if data[2][i] == "Одиночный выбор":
        await Form.start.set()
        for k,j in enumerate(data[3][i].split(",")):
            text = str(j.strip())
            call_back = "active_"+ str(k)
            inline_kb_form.add(types.InlineKeyboardButton(text=text, callback_data=call_back))
    else:
        await Form.form_input.set()
    if data[4][i] != "":
        await bot.send_photo(message.from_user.id, data[4][i])
    await bot.send_message(message.from_user.id, data[1][i], reply_markup=inline_kb_form)


@dp.callback_query_handler(lambda c: c.data.split("_")[0] == "endForm", state="Form:form_end")
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    # Write to state data from callback query
    # get data from state and insert to database
    datas = await state.get_data()
    answers = datas["answers"]
    # Get questions from csv file
    record = await state.get_data()
    record = record["record"]
    with open(record, 'r') as f:
        reader = csv.reader(f)
        data = list(reader)
    qeustions = data[1]
    sql = '''INSERT INTO "''' + record.split(".")[0].split("/")[1].replace(" ", "_") + '''" '''
    sql += "( user_id,"
    for i in qeustions:
        if i == "Вопрос":
            continue
        sql += i.replace(" ", "_") + ", "
    sql = sql[:-2]
    sql += ") VALUES ( "
    user_id = callback_query.from_user.id
    sql += str(user_id) + ", "
    for i in answers:
        if type(i) == list:
            # COnvert list to string
            i = ",".join(i)
        sql += "'" + i.replace(" ", "_") + "', "
    sql = sql[:-2]
    sql += ");"
    print(sql)
    connection, cursor = await connect()
    cursor.execute(sql)
    connection.commit()
    # Get profile from database
    cursor.execute("SELECT promo FROM promos;")
    promos = []
    for row in cursor:
        promos.append(row[0])
    await bot.send_message(callback_query.from_user.id, "Ваши ответы успешно отправлены \nВаш проокд: " + str(random.choice(promos)))

# Callback handler
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

@dp.callback_query_handler(lambda c: c.data == "promo", state="Admin:start")
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await Admin.promo_choose.set()
    inline_kb_promo = types.InlineKeyboardMarkup()
    inline_kb_promo.add(types.InlineKeyboardButton(text="Добавить", callback_data="add_promo"))
    inline_kb_promo.add(types.InlineKeyboardButton(text="Удалить", callback_data="delete_promo"))
    await bot.send_message(callback_query.from_user.id, "Выберите действие", reply_markup=inline_kb_promo)

@dp.callback_query_handler(lambda c: c.data == "add_promo", state="Admin:promo_choose")
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await Admin.promo.set()
    await bot.send_message(callback_query.from_user.id, "Введите промокод")

@dp.callback_query_handler(lambda c: c.data == "delete_promo", state="Admin:promo_choose")
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await Admin.promo_delete.set()
    # Get promos from database
    connection, cursor = await connect()
    cursor.execute("SELECT * FROM promos;")
    promos = []
    for row in cursor:
        promos.append(row[1])
    inline_kb_promo = types.InlineKeyboardMarkup()
    for i in promos:
        inline_kb_promo.add(types.InlineKeyboardButton(text=i, callback_data="delete_" + i))
    inline_kb_promo.add(types.InlineKeyboardButton(text="Назад", callback_data="exit"))
    await bot.send_message(callback_query.from_user.id, "Выберите промокод", reply_markup=inline_kb_promo)

@dp.callback_query_handler(lambda c: c.data.startswith("delete_"), state="Admin:promo_delete")
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    promo = callback_query.data.split("_")[1]
    # Delete promo from database
    connection, cursor = await connect()
    cursor.execute("DELETE FROM promos WHERE promo = '" + promo + "';")
    connection.commit()
    await Admin.promo_delete.set()
    # Get promos from database
    connection, cursor = await connect()
    cursor.execute("SELECT * FROM promos;")
    promos = []
    for row in cursor:
        promos.append(row[1])
    inline_kb_promo = types.InlineKeyboardMarkup()
    for i in promos:
        inline_kb_promo.add(types.InlineKeyboardButton(text=i, callback_data="delete_" + i))
    inline_kb_promo.add(types.InlineKeyboardButton(text="Назад", callback_data="exit"))
    await bot.send_message(callback_query.from_user.id, "Выберите промокод", reply_markup=inline_kb_promo)

@dp.callback_query_handler(lambda c: c.data == "exit", state="Admin:promo_delete")
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await Admin.start.set()
    await bot.send_message(callback_query.from_user.id, "Вы вошли как админ", reply_markup=inline_kb_admin)

@dp.message_handler(state="Admin:promo")
async def process_callback_button1(message: types.Message, state: FSMContext):
    # Save promo code to database
    connection, cursor = await connect()
    cursor.execute("INSERT INTO promos (promo) VALUES ('" + message.text + "');")
    connection.commit()
    await Admin.start.set()
    await bot.send_message(message.from_user.id, "Промокод успешно добавлен", reply_markup=inline_kb_admin)

@dp.callback_query_handler(lambda c: c.data == "exit", state="*")
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await Main.start.set()
    await bot.send_message(callback_query.from_user.id, "Вы вышли из админки", reply_markup=inline_kb_login)

@dp.callback_query_handler(lambda c: c.data == "admins", state="Admin:start")
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await Admin.admins.set()
    # Add inline keyboard with "Добавить администратора" and "Удалить администратора"
    inline_kb_admin = types.InlineKeyboardMarkup()
    inline_kb_admin.add(types.InlineKeyboardButton(text="Добавить администратора", callback_data="add_admin"))
    inline_kb_admin.add(types.InlineKeyboardButton(text="Удалить администратора", callback_data="delete_admin"))
    await bot.send_message(callback_query.from_user.id, "Выберите действие", reply_markup=inline_kb_admin)
        
@dp.callback_query_handler(lambda c: c.data == "add_admin", state="Admin:admins")
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await Admin.add_admin.set()
    await bot.send_message(callback_query.from_user.id, "Введите username администратора после @")

@dp.callback_query_handler(lambda c: c.data == "delete_admin", state="Admin:admins")
async def process_callback_button1(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await Admin.delete_admin.set()
    await bot.send_message(callback_query.from_user.id, "Введите username администратора после @")

@dp.message_handler(state="Admin:add_admin")
async def process_callback_button1(message: types.Message, state: FSMContext):
    admin = message.text
    # Insert admin to database
    connection, cursor = await connect()
    cursor.execute("INSERT INTO admin (admin_id) VALUES ('" + admin + "');")
    connection.commit()
    await Admin.start.set()
    await bot.send_message(message.from_user.id, "Администратор добавлен", reply_markup=inline_kb_admin)

@dp.message_handler(state="Admin:delete_admin")
async def process_callback_button1(message: types.Message, state: FSMContext):
    admin = message.text
    # Delete admin from database
    connection, cursor = await connect()
    cursor.execute("DELETE FROM admin WHERE admin_id='" + admin + "';")
    connection.commit()
    await Admin.start.set()
    await bot.send_message(message.from_user.id, "Администратор удален", reply_markup=inline_kb_admin)    


@dp.callback_query_handler(lambda c: c.data == "login_client", state="Main:login")
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await Client.start.set()
    await bot.send_message(callback_query.from_user.id, "Вы вошли как клиент")

@dp.callback_query_handler(lambda c: c.data == "create_form", state="Admin:start")
async def new_form_add(callback_query: types.CallbackQuery):
    await Admin.new_form.set()
    await bot.send_message(callback_query.from_user.id, "Отправьте файл в формате csv с разделением в ',' \n пример файла: https://docs.google.com/spreadsheets/d/1RgDCazJDDctLQPWPXv9UkT_zfFCtr_DMtGRkvnmhXKY")

# Read from received csv file and create a list of values
@dp.message_handler(content_types=types.ContentTypes.DOCUMENT, state="Admin:new_form")
async def handle_docs_photo(message: types.Message):
    try:
        file_info = await bot.get_file(message.document.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        # Get file name
        src = "forms/" + message.document.file_name
        print(src)
        # Check if file exists
        with open(src, 'wb') as new_file:
            # Write file buffer to file
            new_file.write(downloaded_file.getbuffer())
        # Read from cvs file and create a list of values
        with open(src, 'r') as f:
            reader = csv.reader(f)
            data = list(reader)
        for i in data[2]:
            if i not in ["Тип ячейки", "Одиночный выбор", "Число", "Свободный текст"]:
                os.remove(src)
                raise Exception("Ошибка в указании типа поля, пожалуйста проверьте файл" + i)
        if os.path.exists("forms/" + data[0][1] + ".csv"):
            raise Exception("Такой опросник уже существует, пожалуйста удалите существующий или перименуйте новый")
        os.rename(src,"forms/" + data[0][1] + ".csv")
        # Insert to database
        # Generate hash
        connection,cursor = await connect()
        print("Connected to database")
        path = "forms/" + data[0][1] + ".csv"
        print(path)
        print(type(str(path)))
        cursor.execute("INSERT INTO forms (form_path) VALUES ('"+path+"')")
        print("Form added to database")
        connection.commit()
        # Create database for accepted answers
        # Get questions from csv file
        questions = data[1]
        sql = "CREATE TABLE " + data[0][1].replace(" ", "_") + " (id SERIAL PRIMARY KEY, user_id INTEGER, "
        for i in questions:
            sql += str(i).replace(" ", "_") + " TEXT, "
        sql = sql[:-2] + ");"
        print(sql)
        cursor.execute(sql)
        connection.commit()
        print("Form added to database")
        await Admin.start.set()
        await message.reply("Форма успешно добавлена" , reply_markup=inline_kb_admin)
    except Exception as e:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Отмена", callback_data="cancel"))
        await message.reply(str(e) + " \n - Ошибка при добавлении формы проверьте правильность файла", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == "forms_all", state="Admin:start")
async def process_callback_button1(callback_query: types.CallbackQuery):
    await Admin.forms_all.set()
    forms = os.listdir('forms')
    forms = [i[:-4] for i in forms if i.endswith(".csv")]
    # Add inline keyboard
    markup = types.InlineKeyboardMarkup()
    for i in forms:
        markup.add(types.InlineKeyboardButton(text=i, callback_data=i + "_form"))
    markup.add(types.InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    await bot.send_message(callback_query.from_user.id, "Список всех форм", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.endswith("_form"), state="Admin:forms_all")
async def process_callback_button1(callback_query: types.CallbackQuery):
    await Admin.form_info.set()
    form = callback_query.data[:-5]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Удалить", callback_data=form + "_delete"))
    markup.add(types.InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    markup.add(types.InlineKeyboardButton(text="Получить ссылку на форму", callback_data=form + "_link"))
    markup.add(types.InlineKeyboardButton(text="Скачать результаты", callback_data=form + "_download"))
    await bot.send_message(callback_query.from_user.id, "Форма " + form + "\n", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.endswith("_download"), state="Admin:form_info")
async def process_callback_button1(callback_query: types.CallbackQuery):
    await Admin.start.set()
    form = callback_query.data[:-9]
    # Get id of form
    connection,cursor = await connect()
    cursor.execute("SELECT id FROM forms WHERE form_path = 'forms/" + form + ".csv'")
    form_id = cursor.fetchall()[-1][0]
    # Get questions from csv file
    questions = []
    # Get questions from database names of columns
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = '" + form.replace(" ", "_") + "'")
    questions = cursor.fetchall()
    questions = [i[0] for i in questions[2:]]
    # Get answers from database
    cursor.execute("SELECT * FROM " + form.replace(" ", "_"))
    answers = cursor.fetchall()
    # Create csv file
    with open("results/" + form + "_results.csv", "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(questions)
        for i in answers:
            writer.writerow(i[2:])
    # Send csv file
    # csv to excel
    wb = Workbook()
    ws = wb.active
    with open("results/" + form + "_results.csv", "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            ws.append(row)
    wb.save("results/" + form + "_results.xlsx")
    # Send excel file
    # Reply keyboard
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Вернуться в меню администратора", callback_data="admin"))
    await bot.send_document(callback_query.from_user.id, open("results/" + form + "_results.xlsx", "rb"), reply_markup=markup)
    # await bot.send_document(callback_query.from_user.id, open("results/" + form + "_results.csv", "rb"), reply_markup=types.InlineKeyboardButton(text="Вернуться в меню администратора", callback_data="admin"))

@dp.callback_query_handler(lambda c: c.data.endswith("_link"), state="Admin:form_info")
async def process_callback_button1(callback_query: types.CallbackQuery):
    await Admin.start.set()
    form = callback_query.data[:-5]
    botik = await bot.get_me()
    botik_username = botik.username
    # Get id of form
    connection,cursor = await connect()
    cursor.execute("SELECT id FROM forms WHERE form_path = 'forms/" + form + ".csv'")
    form_id = cursor.fetchall()[-1][0]
    # пример данных
    data = "https://t.me/" + botik_username + "?start=form_" + str(form_id)
    # имя конечного файла
    filename = "site.png"
    # генерируем qr-код
    img = qrcode.make(data)
    # сохраняем img в файл
    img.save(filename)
    # Отправляем qr-код
    await bot.send_photo(callback_query.from_user.id, open(filename, "rb"))
    await bot.send_message(callback_query.from_user.id, "Ссылка на форму " + form + ":\n" + "https://t.me/" + botik_username + "?start=form_" + str(form_id), reply_markup=inline_kb_admin)

@dp.callback_query_handler(lambda c: c.data.endswith("_delete"), state="Admin:form_info")
async def process_callback_button1(callback_query: types.CallbackQuery):
    await Admin.start.set()
    form = callback_query.data[:-7]
    os.remove("forms/" + form + ".csv")
    await bot.send_message(callback_query.from_user.id, "Форма " + form + " удалена", reply_markup=inline_kb_admin)

@dp.callback_query_handler(lambda c: c.data == "cancel", state=["Admin:form_info","Admin:forms_all", "Admin:new_form"])
async def process_callback_button1(callback_query: types.CallbackQuery):
    await Admin.start.set()
    await bot.send_message(callback_query.from_user.id, "Отмена", reply_markup=inline_kb_admin)

@dp.callback_query_handler(lambda c: c.data == "upload_photo", state="Admin:start")
async def process_callback_button1(callback_query: types.CallbackQuery):
    await Admin.upload_photo.set()
    await bot.send_message(callback_query.from_user.id, "Отправьте фотографии которые хотите загрузить в бота")

# Get image from user and return image path in telegram
@dp.message_handler(content_types=types.ContentTypes.PHOTO, state="Admin:upload_photo")
async def get_photo(message: types.Message, state: FSMContext):
    # SAVE IMAGE
    # Get image id
    image_id = message.photo[-1].file_id
    # Send image id to user
    # Button to get back to admin menu
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Вернуться в меню администратора", callback_data="admin"))
    await message.reply("Ваше фото сохранено под id: " + image_id, reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == "admin", state=["Admin:upload_photo","Admin:start"])
async def process_callback_button1(callback_query: types.CallbackQuery):
    await Admin.start.set()
    await bot.send_message(callback_query.from_user.id, "Вернулись в меню администратора", reply_markup=inline_kb_admin)

# Start long polling
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

# Create tables in postgresql form table in postgresql with id (int, autoincrement), form path (text), form hash (text)
# CREATE TABLE forms (id SERIAL PRIMARY KEY, form_path text);
# CREATE TABLE admin (id SERIAL PRIMARY KEY, admin_id text);
# CREATE TABLE promos (id SERIAL PRIMARY KEY, promo text);