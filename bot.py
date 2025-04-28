import logging
import asyncio
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка токена из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Хранилище спам-слов
SPAM_WORDS_FILE = "spam_words.txt"
spam_words = set()

def load_spam_words():
    if os.path.exists(SPAM_WORDS_FILE):
        with open(SPAM_WORDS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                spam_words.add(line.strip().lower())

def save_spam_words():
    with open(SPAM_WORDS_FILE, "w", encoding="utf-8") as f:
        for word in sorted(spam_words):
            f.write(word + "\n")

# Загрузка спам-слов при старте
load_spam_words()

async def add_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Укажите слова для добавления в спам.")
        return
    new_words = [word.lower() for word in context.args]
    spam_words.update(new_words)
    save_spam_words()
    await update.message.reply_text(f"✅ Добавлены в спам: {', '.join(new_words)}")

async def remove_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Укажите слова для удаления из спама.")
        return
    removed = []
    for word in context.args:
        word_lower = word.lower()
        if word_lower in spam_words:
            spam_words.remove(word_lower)
            removed.append(word_lower)
    save_spam_words()
    if removed:
        await update.message.reply_text(f"✅ Удалены из спама: {', '.join(removed)}")
    else:
        await update.message.reply_text("❌ Ничего не найдено для удаления.")

async def list_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if spam_words:
        await update.message.reply_text(f"📋 Список спам-слов:\n" + "\n".join(sorted(spam_words)))
    else:
        await update.message.reply_text("📋 Список спам-слов пуст.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    message_text = update.message.text.lower() if update.message.text else ""
    is_spam = any(word in message_text for word in spam_words)

    if is_spam:
        try:
            await context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
            logger.info(f"💬 Удалено сообщение: {update.message.text}")
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения: {e}")

async def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("spam", add_spam))
    application.add_handler(CommandHandler("unspam", remove_spam))
    application.add_handler(CommandHandler("spamlist", list_spam))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    logger.info("🤖 Бот запущен!")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
