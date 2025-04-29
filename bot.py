import os
import logging
from telegram import Update, MessageEntity
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

# Хранилище спам-слов и чатов
spam_words = set()
known_chats = set()


async def handle_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Please provide a word or phrase to add to spam.")
        return
    phrase = " ".join(context.args).lower()
    spam_words.add(phrase)
    await update.message.reply_text(f"🚫 Added to spam: {phrase}")


async def handle_unspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Please provide a word or phrase to remove from spam.")
        return
    phrase = " ".join(context.args).lower()
    spam_words.discard(phrase)
    await update.message.reply_text(f"✅ Removed from spam: {phrase}")


async def handle_spamlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not spam_words:
        await update.message.reply_text("📭 Spam list is empty.")
    else:
        await update.message.reply_text("📃 Spam phrases:\n" + "\n".join(spam_words))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat_id = update.effective_chat.id
    known_chats.add(chat_id)

    # Проверяем всё содержимое сообщения
    full_text = ""
    if message.text:
        full_text += message.text.lower()
    if message.caption:
        full_text += " " + message.caption.lower()
    if message.reply_to_message and message.reply_to_message.text:
        full_text += " " + message.reply_to_message.text.lower()
    if message.forward_from and message.text:
        full_text += " " + message.text.lower()

    for word in spam_words:
        if word in full_text:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                logger.info(f"💔 Deleted message for spam: {word}")
            except Exception as e:
                logger.error(f"❌ Error deleting message: {e}")
            break


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Provide a message for broadcast.")
        return
    message = " ".join(context.args)
    failed = 0

    for chat_id in list(known_chats):
        try:
            await context.bot.send_message(chat_id, message)
        except Exception as e:
            logger.warning(f"Couldn't send to {chat_id}: {e}")
            failed += 1

    await update.message.reply_text(f"📣 Broadcast sent. Failed: {failed}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("spam", handle_spam))
    app.add_handler(CommandHandler("unspam", handle_unspam))
    app.add_handler(CommandHandler("spamlist", handle_spamlist))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Bot is running...")
    app.run_polling()
