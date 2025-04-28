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
    spam_word = " ".join(context.args).lower()
    spam_words.add(spam_word)
    await update.message.reply_text(f"🚫 Добавлено в спам: {spam_word}")

# Обработчик команды /unspam
async def handle_unspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи слово для удаления из спама.")
        return
    spam_word = " ".join(context.args).lower()
    spam_words.discard(spam_word)
    await update.message.reply_text(f"✅ Удалено из спама: {spam_word}")

# Обработчик команды /spamlist
async def handle_spamlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not spam_words:
        await update.message.reply_text("📭 Список спам-слов пуст.")
    else:
        await update.message.reply_text("📃 Спам-слова: " + ", ".join(spam_words))

# Извлечение текста из сообщения
def extract_text(message):
    if message.text:
        return message.text
    if message.caption:
        return message.caption
    return ""

# Основной фильтр сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    msg_text = extract_text(message).lower()

    # Проверка основного сообщения
    should_delete = any(spam_word in msg_text for spam_word in spam_words)

    # Проверка текста в сообщении, на которое ответили
    if message.reply_to_message:
        replied_text = extract_text(message.reply_to_message).lower()
        if any(spam_word in replied_text for spam_word in spam_words):
            should_delete = True
            try:
                await context.bot.delete_message(chat_id=message.chat_id,
                                                 message_id=message.reply_to_message.message_id)
                logger.info(f"💔 Удалено сообщение-ответ: {replied_text}")
            except Exception as e:
                logger.error(f"Ошибка при удалении ответа: {e}")

    if should_delete:
        try:
            await context.bot.delete_message(chat_id=message.chat_id,
                                             message_id=message.message_id)
            logger.info(f"💔 Удалено сообщение: {msg_text}")
        except Exception as e:
            logger.error(f"Ошибка при удалении: {e}")

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("spam", handle_spam))
    application.add_handler(CommandHandler("unspam", handle_unspam))
    application.add_handler(CommandHandler("spamlist", handle_spamlist))
    application.add_handler(MessageHandler(filters.ALL, handle_message))

    logger.info("🤖 Бот запущен!")
    application.run_polling()
