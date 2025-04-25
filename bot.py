from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import os

BANNED_WORDS = ['спам', 'реклама', 'мат']

async def delete_bad_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and any(word in update.message.text.lower() for word in BANNED_WORDS):
        try:
            await update.message.delete()
        except Exception as e:
            print(f"Ошибка удаления: {e}")

# Безопасный способ — токен из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ BOT_TOKEN не установлен!")
else:
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), delete_bad_messages))
    app.run_polling()
