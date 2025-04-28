import os
import logging
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("bot")

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not found in environment variables")

spam_words = set()

async def handle_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи слово или фразу для добавления в спам.")
        return
    phrase = " ".join(context.args).strip().lower()
    spam_words.add(phrase)
    await update.message.reply_text(f"🚫 Добавлено в спам: {phrase}")

async def handle_unspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи слово или фразу для удаления из спама.")
        return
    phrase = " ".join(context.args).strip().lower()
    spam_words.discard(phrase)
    await update.message.reply_text(f"✅ Удалено из спама: {phrase}")

async def handle_spamlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not spam_words:
        await update.message.reply_text("📭 Список спам-слов пуст.")
    else:
        await update.message.reply_text("📃 Спам-слова: " + ", ".join(spam_words))

def get_text_from_message(message: Message) -> str:
    if message.text:
        return message.text
    elif message.caption:
        return message.caption
    return ""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    # Берем текст из обычного, пересланного или ответного сообщения
    text_to_check = get_text_from_message(message)
    if message.reply_to_message:
        text_to_check += " " + get_text_from_message(message.reply_to_message)
    if message.forward_from or message.forward_sender_name:
        text_to_check += " " + get_text_from_message(message)

    text_to_check = text_to_check.lower()
    logger.info(f"📩 Пришло сообщение: {text_to_check}")

    for spam_word in spam_words:
        if spam_word in text_to_check:
            try:
                await context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
                logger.info(f"💔 Удалено сообщение: {text_to_check}")
            except Exception as e:
                logger.error(f"Ошибка при удалении: {e}")
            break  # Удалили - выходим

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("spam", handle_spam))
    application.add_handler(CommandHandler("unspam", handle_unspam))
    application.add_handler(CommandHandler("spamlist", handle_spamlist))
    application.add_handler(MessageHandler(filters.ALL, handle_message))

    logger.info("🤖 Бот запущен!")
    application.run_polling()
