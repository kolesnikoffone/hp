import os
import logging
from telegram import Update
from telegram.ext import (ApplicationBuilder, ContextTypes, MessageHandler,
                          CommandHandler, filters)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("bot")

# Получение токена
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not found in environment variables")

# Хранилище спам-слов
spam_words = set()

# Обработчик команды /spam
async def handle_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи слово для добавления в спам.")
        return
    for word in context.args:
        spam_words.add(word.lower())
    await update.message.reply_text(f"🚫 Добавлено в спам: {context.args}")

# Обработчик команды /unspam
async def handle_unspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи слово для удаления из спама.")
        return
    for word in context.args:
        spam_words.discard(word.lower())
    await update.message.reply_text(f"✅ Удалено из спама: {context.args}")

# Обработчик команды /spamlist
async def handle_spamlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not spam_words:
        await update.message.reply_text("📭 Список спам-слов пуст.")
    else:
        await update.message.reply_text("📃 Спам-слова: " + ", ".join(spam_words))

# Основной фильтр сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_text = update.message.text.lower()
    logger.info(f"📩 Пришло сообщение: {msg_text}")
    if any(word in msg_text for word in spam_words):
        try:
            await context.bot.delete_message(chat_id=update.message.chat_id,
                                             message_id=update.message.message_id)
            logger.info(f"💔 Удалено сообщение: {msg_text}")
        except Exception as e:
            logger.error(f"Ошибка при удалении: {e}")

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("spam", handle_spam))
    application.add_handler(CommandHandler("unspam", handle_unspam))
    application.add_handler(CommandHandler("spamlist", handle_spamlist))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Бот запущен!")
    application.run_polling()
