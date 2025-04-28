import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, MessageHandler,
    CommandHandler, filters
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("bot")

# Получение токена
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not found in environment variables")

# Хранилище спам-фраз
spam_words = set()

# Команда /spam — добавить слова в спам
async def handle_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи фразу для добавления в спам.")
        return
    phrase = " ".join(context.args).lower()
    spam_words.add(phrase)
    await update.message.reply_text(f"🚫 Добавлено в спам: {phrase}")

# Команда /unspam — удалить слова из спама
async def handle_unspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи фразу для удаления из спама.")
        return
    phrase = " ".join(context.args).lower()
    if phrase in spam_words:
        spam_words.remove(phrase)
        await update.message.reply_text(f"✅ Удалено из спама: {phrase}")
    else:
        await update.message.reply_text(f"ℹ️ Фраза '{phrase}' не найдена в списке спама.")

# Команда /spamlist — показать все спам-фразы
async def handle_spamlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not spam_words:
        await update.message.reply_text("📭 Список спам-фраз пуст.")
    else:
        await update.message.reply_text("📃 Спам-фразы:\n" + "\n".join(spam_words))

# Основной фильтр сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # Берем текст обычного или пересланного сообщения
    msg_text = ""
    if update.message.text:
        msg_text = update.message.text.lower()
    elif update.message.caption:
        msg_text = update.message.caption.lower()

    logger.info(f"📩 Пришло сообщение: {msg_text}")

    # Проверяем точное вхождение фраз
    for spam_phrase in spam_words:
        if spam_phrase in msg_text:
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
                logger.info(f"💔 Удалено сообщение: {msg_text}")
            except Exception as e:
                logger.error(f"Ошибка при удалении: {e}")
            return  # нашли — остановились

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("spam", handle_spam))
    application.add_handler(CommandHandler("unspam", handle_unspam))
    application.add_handler(CommandHandler("spamlist", handle_spamlist))
    # Обработчик всех текстов
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Бот запущен!")
    application.run_polling()
