import os
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters


async def correct_english(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    await update.message.reply_text(
        f"You wrote:\n{text}\n\n"
        "Your English correction system is working!"
    )


def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN is not set!")

    app = Application.builder().token(token).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, correct_english)
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
