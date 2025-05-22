import asyncio
import json
import logging
import os
import nest_asyncio
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# 🔧 Настройки
TOKEN = "7827265617:AAEQvEsQE-v9gU0IpZZo7eUnUzjeqwawRM0"
ADMIN_USERNAME = "alice_alekseeevna"
EMPLOYEES_FILE = "employees.json"
PORT = int(os.environ.get("PORT", 8443))

# 🔧 Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 📁 Работа с файлами
def load_employees():
    with open(EMPLOYEES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_employees(employees):
    with open(EMPLOYEES_FILE, "w", encoding="utf-8") as f:
        json.dump(employees, f, ensure_ascii=False, indent=2)

# ✅ Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    employees = load_employees()
    for emp in employees:
        if emp["username"] == user.username:
            emp["chat_id"] = user.id
            save_employees(employees)
            await update.message.reply_text("Ты зарегистрирован. Жди уведомления перед сменой.")
            return
    await update.message.reply_text("Ты не в списке сотрудников.")

# 📬 Кнопки "Да" и "Нет"
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    status, username, point = query.data.split("|")
    symbol = "✅" if status == "yes" else "❌"
    text = f"@{username} ({point}) — выходит {symbol}"

    employees = load_employees()
    for emp in employees:
        if emp["username"] == ADMIN_USERNAME and emp.get("chat_id"):
            await context.bot.send_message(emp["chat_id"], text)

# 🔁 Уведомления перед сменой
async def send_notifications(app):
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        employees = load_employees()
        for emp in employees:
            if emp.get("chat_id") and emp.get("open_time"):
                hour, minute = map(int, emp["open_time"].split(":"))
                notify_time = (hour * 60 + minute) - 25
                if notify_time < 0:
                    continue
                notif_hour = notify_time // 60
                notif_minute = notify_time % 60
                if current_time == f"{notif_hour:02d}:{notif_minute:02d}":
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ Да", callback_data=f"yes|{emp['username']}|{emp['point']}"),
                            InlineKeyboardButton("❌ Нет", callback_data=f"no|{emp['username']}|{emp['point']}")
                        ]
                    ])
                    await app.bot.send_message(chat_id=emp["chat_id"], text="Выходишь сегодня на смену?", reply_markup=keyboard)
        await asyncio.sleep(60)

# 🧪 Тест вручную
async def test_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    employees = load_employees()
    for emp in employees:
        if emp["username"] == update.effective_user.username:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Да", callback_data=f"yes|{emp['username']}|{emp['point']}"),
                    InlineKeyboardButton("❌ Нет", callback_data=f"no|{emp['username']}|{emp['point']}")
                ]
            ])
            await update.message.reply_text("Тестовая проверка: выходишь на смену?", reply_markup=keyboard)
            return

# 🚀 Запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_notify))
    app.add_handler(CallbackQueryHandler(button_handler))

    asyncio.create_task(send_notifications(app))

    webhook_url = os.getenv("WEBHOOK_URL")

    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=webhook_url,
        allowed_updates=Update.ALL_TYPES
    )

# ✅ Запуск с nest_asyncio
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
