import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("bot")

# Токен из переменных окружения
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not found in environment variables")

# Хранилище спам-фраз
spam_phrases = set()

# Команда /spam для добавления фраз
async def handle_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    phrase = text.partition(' ')[2].strip()
    if not phrase:
        await update.message.reply_text("❗ Укажи слово или фразу для добавления в спам.")
        return
    spam_phrases.add(phrase.lower())
    await update.message.reply_text(f"🚫 Добавлено в спам: {phrase}")

# Команда /unspam для удаления фраз
async def handle_unspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    phrase = text.partition(' ')[2].strip()
    if not phrase:
        await update.message.reply_text("❗ Укажи слово или фразу для удаления из спама.")
        return
    if phrase.lower() in spam_phrases:
        spam_phrases.remove(phrase.lower())
        await update.message.reply_text(f"✅ Удалено из спама: {phrase}")
    else:
        await update.message.reply_text("📭 Такого слова или фразы нет в списке.")

# Команда /spamlist для отображения списка фраз
async def handle_spamlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not spam_phrases:
        await update.message.reply_text("📭 Список спам-слов пуст.")
    else:
        await update.message.reply_text("📃 Спам-слова и фразы:\n" + "\n".join(spam_phrases))

# Основной обработчик всех сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_text = update.message.text.lower()
    logger.info(f"📩 Пришло сообщение: {msg_text}")
    for phrase in spam_phrases:
        if phrase in msg_text:
            try:
                await context.bot.delete_message(chat_id=update.message.chat_id,
                                                 message_id=update.message.message_id)
                logger.info(f"💔 Удалено сообщение: {msg_text}")
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщения: {e}")
            break

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("spam", handle_spam))
    app.add_handler(CommandHandler("unspam", handle_unspam))
    app.add_handler(CommandHandler("spamlist", handle_spamlist))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Бот запущен!")
    app.run_polling()
