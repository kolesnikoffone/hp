import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, MessageHandler, filters
)

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

# Команда /spam
async def handle_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи слово или фразу для добавления в спам.")
        return
    for word in context.args:
        spam_words.add(word.lower())
    await update.message.reply_text(f"🚫 Добавлено в спам: {context.args}")

# Команда /unspam
async def handle_unspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи слово или фразу для удаления из спама.")
        return
    for word in context.args:
        spam_words.discard(word.lower())
    await update.message.reply_text(f"✅ Удалено из спама: {context.args}")

# Команда /spamlist
async def handle_spamlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not spam_words:
        await update.message.reply_text("📭 Список спам-слов пуст.")
    else:
        await update.message.reply_text("📃 Спам-слова:\n" + "\n".join(spam_words))

# Основной обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    text_variants = []

    if msg.text:
        text_variants.append(msg.text.lower())
    if msg.reply_to_message and msg.reply_to_message.text:
        text_variants.append(msg.reply_to_message.text.lower())
    if msg.forward_date and msg.text:
        text_variants.append(msg.text.lower())

    logger.info(f"📩 Пришло сообщение: {msg.text}")

    for text in text_variants:
        for spam_word in spam_words:
            if spam_word == text or spam_word in text.split():
                try:
                    await context.bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id)
                    logger.info(f"💔 Удалено сообщение за спам-слово '{spam_word}': {text}")
                    return
                except Exception as e:
                    logger.error(f"Ошибка при удалении сообщения: {e}")
                    return

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("spam", handle_spam))
    application.add_handler(CommandHandler("unspam", handle_unspam))
    application.add_handler(CommandHandler("spamlist", handle_spamlist))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Бот запущен!")
    application.run_polling()
