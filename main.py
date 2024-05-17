import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils import executor
from datetime import date

TOKEN = '6993661980:AAE9Cy-BNrTL3AsAyuHxL5oKuus-aJcMyc8'

# Owner ID
OWNER_ID = 732748499

bot = Bot(TOKEN)
dp = Dispatcher(bot)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('bot_stats.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            visits INTEGER NOT NULL DEFAULT 0,
            last_visit TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            date TEXT PRIMARY KEY,
            visits INTEGER NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Функция для обновления структуры базы данных
def update_db_structure():
    conn = sqlite3.connect('bot_stats.db')
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(user_stats)')
    columns = [col[1] for col in cursor.fetchall()]
    if 'last_visit' not in columns:
        cursor.execute('ALTER TABLE user_stats ADD COLUMN last_visit TEXT')
    conn.commit()
    conn.close()

# Функция добавления/обновления статистики пользователя
def update_user_stats(user_id):
    conn = sqlite3.connect('bot_stats.db')
    cursor = conn.cursor()
    today = date.today().isoformat()

    cursor.execute('INSERT OR IGNORE INTO user_stats (user_id, last_visit) VALUES (?, ?)', (user_id, today))
    cursor.execute('UPDATE user_stats SET visits = visits + 1, last_visit = ? WHERE user_id = ?', (today, user_id))

    cursor.execute('INSERT OR IGNORE INTO daily_stats (date) VALUES (?)', (today,))
    cursor.execute('UPDATE daily_stats SET visits = visits + 1 WHERE date = ?', (today,))
    
    conn.commit()
    conn.close()

# Получение общей статистики
async def get_total_stats():
    conn = sqlite3.connect('bot_stats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM user_stats')
    total_users = cursor.fetchone()[0]
    cursor.execute('SELECT SUM(visits) FROM user_stats')
    total_visits = cursor.fetchone()[0]
    conn.close()
    return total_users, total_visits

# Получение статистики за сегодня
async def get_today_stats():
    conn = sqlite3.connect('bot_stats.db')
    cursor = conn.cursor()
    today = date.today().isoformat()
    cursor.execute('SELECT visits FROM daily_stats WHERE date = ?', (today,))
    today_visits = cursor.fetchone()
    conn.close()
    return today_visits[0] if today_visits else 0

# Функция для получения списка пользователей
async def get_users():
    conn = sqlite3.connect('bot_stats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM user_stats')
    users = cursor.fetchall()
    conn.close()
    return users

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    update_user_stats(message.from_user.id)  # Обновляем статистику пользователя
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    button_open_site = KeyboardButton(text='🍔 Сделать Заказ 🍔', web_app=WebAppInfo(url='https://lopezdeniz.github.io/mycart2'))
    button_feedback = KeyboardButton(text='✉️ Обратная связь ✉️')
    markup.add(button_open_site)
    markup.add(button_feedback)

    # Создание кнопки для закреплённого сообщения
    inline_markup = InlineKeyboardMarkup()
    inline_button = InlineKeyboardButton(text="🍔 Сделать Заказ 🍔", web_app=WebAppInfo(url="https://lopezdeniz.github.io/mycart2"))
    inline_markup.add(inline_button)

    sent_message = await message.answer("Добро пожаловать! Нажмите кнопку ниже, чтобы открыть сайт или для обратной связи.", reply_markup=markup)

    # Отправка и закрепление сообщения с кнопкой
    pinned_message = await message.answer("Закреплённое сообщение с кнопкой:", reply_markup=inline_markup)
    await bot.pin_chat_message(chat_id=message.chat.id, message_id=pinned_message.message_id)

@dp.message_handler(lambda message: 'Обратная связь' in message.text)
async def handle_feedback(message: types.Message):
    update_user_stats(message.from_user.id)  # Обновляем статистику пользователя при нажатии на кнопку обратной связи
    await message.answer("Нажмите здесь, чтобы начать чат со мной: https://t.me/LopezDeniz")

@dp.message_handler(commands=['users'])
async def users_list(message: types.Message):
    if message.from_user.id == OWNER_ID:
        users = await get_users()
        if users:
            users_info = "\n".join([str(user[0]) for user in users])
            await message.answer(f"Список пользователей бота:\n{users_info}")
        else:
            await message.answer("Пользователей пока нет.")
    else:
        await message.answer('У вас нет доступа к этой команде.')

@dp.message_handler(commands=['stats'])
async def stats(message: types.Message):
    if message.from_user.id == OWNER_ID:
        total_users, total_visits = await get_total_stats()
        today_visits = await get_today_stats()
        stats_message = (
            f"📊 <b>Статистика бота:</b>\n"
            f"👥 <b>Активные пользователи:</b> {total_users}\n"
            f"🔢 <b>Всего посещений:</b> {total_visits}\n"
            f"📅 <b>Посещений сегодня:</b> {today_visits}"
        )
        await message.answer(stats_message, parse_mode=types.ParseMode.HTML)
    else:
        await message.answer('У вас нет доступа к этой команде.')

@dp.message_handler(commands=['commands'])
async def list_commands(message: types.Message):
    if message.from_user.id == OWNER_ID:
        commands_message = (
            "📝 <b>Список доступных команд:</b>\n"
            "/start - Начать работу с ботом\n"
            "/users - Список пользователей\n"
            "/stats - Статистика бота\n"
            "/commands - Список всех команд (только для владельца)"
        )
        await message.answer(commands_message, parse_mode=types.ParseMode.HTML)
    else:
        await message.answer('У вас нет доступа к этой команде.')

if __name__ == '__main__':
    init_db()  # Инициализация базы данных при старте
    update_db_structure()  # Обновление структуры базы данных при старте
    executor.start_polling(dp, skip_updates=True)
