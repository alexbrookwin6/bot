import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "7827265617:AAEQvEsQE-v9gU0IpZZo7eUnUzjeqwawRM0"
ADMIN_USERNAME = "alice_alekseeevna"
EMPLOYEES_FILE = "employees.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_employees():
    with open(EMPLOYEES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    employees = load_employees()
    for emp in employees:
        if emp["username"] == user.username:
            emp["chat_id"] = user.id  # Сохраняем chat_id для этого пользователя
            with open(EMPLOYEES_FILE, "w", encoding="utf-8") as f:
                json.dump(employees, f, ensure_ascii=False, indent=2)
            await update.message.reply_text("Ты зарегистрирован. Жди уведомления с кнопками.")
            return
    await update.message.reply_text("Ты не в списке сотрудников.")

async def test_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    employees = load_employees()
    emp = next((e for e in employees if e["username"] == user.username), None)
    if not emp or not emp.get("chat_id"):
        await update.message.reply_text("Сначала используй /start для регистрации.")
        return
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Да", callback_data=f"yes|{emp['username']}|point"),
            InlineKeyboardButton("❌ Нет", callback_data=f"no|{emp['username']}|point"),
        ]
    ])
    await context.bot.send_message(chat_id=emp["chat_id"], text="Выходишь сегодня на смену?", reply_markup=keyboard)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    status, username, point = query.data.split("|")
    symbol = "✅" if status == "yes" else "❌"
    text = f"@{username} — выходит {symbol}"

    employees = load_employees()
    admin = next((emp for emp in employees if emp["username"] == ADMIN_USERNAME and emp.get("chat_id")), None)
    if admin:
        try:
            await context.bot.send_message(admin["chat_id"], text)
            logger.info(f"Отправлено администратору: {text}")
        except Exception as e:
            logger.error(f"Ошибка при отправке администратору: {e}")
    else:
        logger.error("Админ не найден или chat_id не указан")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_buttons))
    app.add_handler(CallbackQueryHandler(button_handler))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
