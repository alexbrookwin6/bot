from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import json
import logging
import asyncio

# Настройки
TOKEN = "7827265617:AAEQvEsQE-v9gU0IpZZo7eUnUzjeqwawRM0"
ADMIN_USERNAME = "alice_alekseeevna"
EMPLOYEES_FILE = "employees.json"

# Логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка списка сотрудников
def load_employees():
    with open(EMPLOYEES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Сохранять не нужно для теста, только загрузка

# Команда /test — отправить кнопки сотруднику
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Да", callback_data="yes|test"),
            InlineKeyboardButton("❌ Нет", callback_data="no|test")
        ]
    ])
    await update.message.reply_text("Выходишь сегодня на смену?", reply_markup=keyboard)

# Обработчик нажатия на кнопку
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    status, action = query.data.split("|")
    user = query.from_user

    symbol = "✅" if status == "yes" else "❌"
    text = f"@{user.username} ответил: {symbol} на {action}"

    # Найти чат id админа и отправить уведомление
    employees = load_employees()
    for emp in employees:
        if emp["username"] == ADMIN_USERNAME and emp.get("chat_id"):
            await context.bot.send_message(emp["chat_id"], text)

# Основная функция запуска бота
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    await app.run_polling()

import nest_asyncio
nest_asyncio.apply()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
