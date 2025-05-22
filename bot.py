import logging
import datetime
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CallbackQueryHandler, CommandHandler
)

# Токен и настройки
TOKEN = "7827265617:AAHryeg05P_C4bGVn6toI6i6gAKhHSkSjzo"
ADMIN_USERNAME = "alice_alekseeevna"
STAFF = [
    {
        "username": "alice_alekseeevna",
        "chat_id": None,  # будет заполнено при первом запуске
        "point": "Тестовая точка",
        "open_time": "12:00"
    }
]

# Логгинг
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    for staff in STAFF:
        if staff["username"] == user.username:
            staff["chat_id"] = user.id
            await update.message.reply_text("Ты зарегистрирован как сотрудник. Жди уведомления утром.")
            return
    await update.message.reply_text("Ты не в списке сотрудников.")

# Рассылка утреннего вопроса
async def send_daily_notifications(app):
    while True:
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")

        for staff in STAFF:
            if staff["chat_id"] and staff["open_time"] == "12:00" and current_time == "11:55":
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Да", callback_data=f"yes|{staff['username']}|{staff['point']}"),
                        InlineKeyboardButton("❌ Нет", callback_data=f"no|{staff['username']}|{staff['point']}")
                    ]
                ])
                try:
                    await app.bot.send_message(
                        chat_id=staff["chat_id"],
                        text="Выходишь сегодня на смену?",
                        reply_markup=keyboard
                    )
                except Exception as e:
                    print(f"Ошибка при отправке: {e}")
        await asyncio.sleep(60)  # Проверять каждую минуту

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    status, username, point = data
    symbol = "✅" if status == "yes" else "❌"

    message = f"@{username} ({point}) — выходит {symbol}"

    admin_id = None
    for staff in STAFF:
        if staff["username"] == ADMIN_USERNAME:
            admin_id = staff["chat_id"]

    if admin_id:
        await context.bot.send_message(chat_id=admin_id, text=message)

# Основной запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Удаляем Webhook перед polling
    await app.bot.delete_webhook(drop_pending_updates=True)

    # Запуск фоновой задачи
    asyncio.create_task(send_daily_notifications(app))

    print("Бот запускается...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
