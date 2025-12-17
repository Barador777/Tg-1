import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

TOKEN = ""
ADMIN_IDS = []
CHANGE_NAME = 1

QUOTES = [
    "Работа — не волк. Работа — это ворк, а волк — это ходить",
    "Шаг влево, шаг вправо — два шага",
    "Если закрыть глаза, становится темно",
    "Если долго смотреть на огонь, то тебя уволят из МЧС",
    "Запомни: одна ошибка — и ты ошибся",
    "Жи-ши пиши от души",
    "Если тебе где-то не рады, значит, ты там не нужен. А если тебе где-то рады, значит, ты там еще не накосячил",
    "Если работа мешает отдыху — бросай работу. Если отдых мешает работе — бросай пить",
    "Кто рано встает, тот потом весь день хочет спать",
    "Сделал дело — гуляй смело. Не сделал дело — гуляй еще смелее, все равно уже ничего не изменишь",
    "Не слушай тех, кто говорит, что ты неудачник. Слушай тех, кто молчит — они хотя бы не бесят",
    "Если тебе плюют в спину, значит, ты идешь впереди. Либо ты в очереди за шаурмой и за тобой стоит верблюд",
    "Не ищи смысл там, где его нет. И там, где он есть, тоже не ищи — время потеряешь",
    "Если штанга не идет к Джейсону, Джейсон идет за пивом",
    "Бег — это жизнь. Особенно если за тобой бежит медведь"
]

def init_db():
    conn = sqlite3.connect('Tg_Bot_Registr.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Пользователи (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_user INTEGER UNIQUE,
        first_name TEXT NOT NULL,
        user_name TEXT NOT NULL,
        last_name TEXT
    )''')
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Регистрация", callback_data='reg')],
        [InlineKeyboardButton("Изменить имя", callback_data='change_name')],
        [InlineKeyboardButton("Случайная цитата", callback_data='random_quote')]
    ]
    await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'reg':
        user = query.from_user
        conn = sqlite3.connect('Tg_Bot_Registr.db')
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM Пользователи WHERE id_user = ?', (user.id,))

        if cursor.fetchone():
            text = "Вы уже зарегистрированы"
        else:
            cursor.execute('INSERT INTO Пользователи(id_user, first_name, user_name, last_name) VALUES (?, ?, ?, ?)',
                           (user.id, user.first_name, user.username or "", user.last_name or ""))
            conn.commit()
            text = f"Вы успешно зарегистрированы, {user.first_name}!"

        conn.close()
        await query.edit_message_text(text=text)

    elif query.data == 'random_quote':
        quote = random.choice(QUOTES)
        text = f"Случайная цитата:\n\n«{quote}»"
        await query.edit_message_text(text=text)

async def change_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    conn = sqlite3.connect('Tg_Bot_Registr.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM Пользователи WHERE id_user = ?', (user_id,))

    if not cursor.fetchone():
        await query.edit_message_text(text="Сначала зарегистрируйтесь!")
        conn.close()
        return ConversationHandler.END

    conn.close()
    await query.edit_message_text(text="Введите имя и фамилию через пробел (например: Иван Иванов) или свой псевданим:")
    return CHANGE_NAME

async def change_name_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    full_name = update.message.text.strip().split()

    conn = sqlite3.connect('Tg_Bot_Registr.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE Пользователи SET first_name = ?, last_name = ? WHERE id_user = ?',
    (full_name[0], " ".join(full_name[1:]), user_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Данные обновлены! Теперь вас зовут: {full_name[0]} {' '.join(full_name[1:])}")
    return ConversationHandler.END

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступ запрещен.")
        return

    conn = sqlite3.connect('Tg_Bot_Registr.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id_user, first_name, last_name, user_name FROM Пользователи')
    users = cursor.fetchall()
    conn.close()

    if not users:
        await update.message.reply_text("Нет пользователей.")
        return

    message = "Список пользователей:\n\n"
    for i, (uid, first, last, username) in enumerate(users, 1):
        message += f"{i}. ID: {uid}\n"
        message += f"   Имя: {first}\n"
        message += f"   Фамилия: {last or 'Нет'}\n"
        message += f"   Username: @{username if username else 'нет'}\n\n"
    await update.message.reply_text(message)

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('admin', admin_panel))
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^(reg|random_quote)$'))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(change_name_start, pattern='^change_name$')],
        states={
            CHANGE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_name_process)]
        },
        fallbacks=[],
        per_message=False
    )
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()