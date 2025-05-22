import logging
import asyncio
import json
import httpx
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# 🔧 НАСТРОЙКИ
TOKEN = "7827265617:AAEQvEsQE-v9gU0IpZZo7eUnUzjeqwawRM0"
ADMIN_USERNAME = "alice_alekseeevna"
EMPLOYEES_FILE = "employees.json"

# 🔧 ЛОГИ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 📦 ЗАГРУЗКА ДАННЫХ
def load_employees():
    with open(EMPLOYEES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_employees(employees):
    with open(EMPLOYEES_FILE, "w", encoding="utf-8") as f:
        json.dump(employees, f, ensure_ascii=False, indent=2)

# ✅ /start
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

# 👇 Ответ на кнопку
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

# 📬 Рассылка утром
async def send_notifications(app):
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        employees = load_employees()
        for emp in employees:
            if emp["chat_id"] and emp["open_time"]:
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
                    try:
                        await app.bot.send_message(chat_id=emp["chat_id"], text="Выходишь сегодня на смену?", reply_markup=keyboard)
                    except Exception as e:
                        logger.warning(f"Ошибка при отправке: {e}")
        await asyncio.sleep(60)
        
# 📤 Отключение старого Webhook (если был)
async def delete_webhook():
    async with httpx.AsyncClient() as client:
        await client.post(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")

# 🚀 Запуск
async def main():
    await delete_webhook()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    asyncio.create_task(send_notifications(app))
    await app.run_polling()

import nest_asyncio
nest_asyncio.apply()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
