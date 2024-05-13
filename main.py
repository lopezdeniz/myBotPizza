import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.utils import executor

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
            visits INTEGER NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Функция добавления/обновления статистики пользователя
def update_user_stats(user_id):
    conn = sqlite3.connect('bot_stats.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)', (user_id,))
    cursor.execute('UPDATE user_stats SET visits = visits + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# Получение статистики
async def get_stats():
    conn = sqlite3.connect('bot_stats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM user_stats')
    total_users = cursor.fetchone()[0]
    cursor.execute('SELECT SUM(visits) FROM user_stats')
    total_visits = cursor.fetchone()[0]
    conn.close()
    return total_users, total_visits

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
    button_open_site = KeyboardButton(text='🍔 Открыть веб-страницу 🍔', web_app=WebAppInfo(url='https://lopezdeniz.github.io/my-cart/'))
    button_feedback = KeyboardButton(text='✉️ Обратная связь ✉️')
    markup.add(button_open_site)
    markup.add(button_feedback)
    await message.answer("Добро пожаловать! Нажмите кнопку ниже, чтобы открыть сайт или для обратной связи.", reply_markup=markup)

@dp.message_handler(lambda message: 'Обратная связь' in message.text)
async def handle_feedback(message: types.Message):
    # Используйте ваш настоящий идентификатор чата либо username.
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
        total_users, total_visits = await get_stats()
        stats_message = (
            f"📊 <b>Статистика бота:</b>\n"
            f"👥 <b>Активные пользователи:</b> {total_users}\n"
            f"🔢 <b>Всего посещений:</b> {total_visits}"
        )
        await message.answer(stats_message, parse_mode=types.ParseMode.HTML)
    else:
        await message.answer('У вас нет доступа к этой команде.')

if __name__ == '__main__':
    init_db()  # Инициализация базы данных при старте
    executor.start_polling(dp, skip_updates=True)

