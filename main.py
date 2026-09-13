import os
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from google import genai

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

PROMPT = """
You are an English correction assistant in a Telegram group.

Check the user's English message for:
1. Grammar mistakes
2. Spelling mistakes
3. Unnatural or awkward English phrasing

Keep the user's original meaning, tone, and level.
Do not rewrite correct and natural sentences unnecessarily.

If the sentence is already correct and natural, reply with exactly:
NO_CORRECTION

If there is a problem, reply in this format:

Correction:
[corrected sentence]

Why:
[short, simple explanation of the important correction]

User's message:
"""


async def correct_english(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if not text:
        return

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=PROMPT + text
        )

        result = response.text.strip()

        if result != "NO_CORRECTION":
            await update.message.reply_text(result)

    except Exception as e:
        print("Error:", e)


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set!")

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, correct_english)
    )

    print("English Correction Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
