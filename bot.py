import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 🔧 Настройка логгера
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("bot")

# 🔐 Получение токена и ID админа из переменных окружения
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

# 🗂 Хранилище всех чатов
chat_ids = set()

# 🧩 Сохраняем ID чата при любом сообщении
async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_ids.add(chat_id)
    logger.info(f"📥 Отслеживаем чат: {chat_id}")

# 🚀 Команда для рассылки сообщений от админа
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Только админ может использовать эту команду.")
        return

    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("❗ Укажи сообщение для рассылки.")
        return

    count = 0
    for chat_id in chat_ids:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            count += 1
        except Exception as e:
            logger.error(f"❌ Не удалось отправить в {chat_id}: {e}")
    await update.message.reply_text(f"✅ Рассылка отправлена в {count} чатов.")

# ▶️ Запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # Команда /рассылка
    app.add_handler(CommandHandler("broadcast", broadcast))

    # Любое сообщение — отслеживаем чат
    app.add_handler(MessageHandler(filters.ALL, track_chats))

    logger.info("🤖 Бот запущен!")
    app.run_polling()
