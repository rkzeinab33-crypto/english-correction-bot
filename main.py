import os
import re
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from groq import Groq

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are an English correction assistant in a Telegram group.

Your job is to detect clear English mistakes.

Check for:
- Grammar mistakes
- Spelling mistakes
- Clearly unnatural English phrasing

IMPORTANT:
Do NOT correct sentences just because you would phrase them differently.
Do NOT rewrite natural casual English.
Keep the user's meaning, tone, and approximate English level.

Short English sentences can still contain important mistakes, so check them when they look like actual sentences.

If the message is correct and natural, respond with exactly:
NO_CORRECTION

If there is a clear mistake, respond with ONLY the corrected sentence.

Do not explain the mistake.
Do not use "Correction:".
Do not add quotation marks.
Do not discuss anything else.
"""


def should_check(text):
    text = text.strip()

    if not text:
        return False

    # Ignore very short casual replies that normally don't need correction
    casual_replies = {
        "ok", "okay", "yeah", "yes", "no", "sure",
        "thanks", "thank you", "exactly", "of course",
        "i think so", "me too", "me neither",
        "that's good", "it's good", "sounds good",
        "that's great", "very good", "good idea"
    }

    normalized = re.sub(r"[.!?,]+$", "", text.lower()).strip()

    if normalized in casual_replies:
        return False

    # Ignore messages that are only URLs
    if re.fullmatch(r"https?://\S+", text):
        return False

    # Ignore messages with no English letters
    english_letters = len(re.findall(r"[A-Za-z]", text))

    if english_letters == 0:
        return False

    # Ignore messages that are mostly Persian/non-English
    all_letters = len(re.findall(r"[A-Za-z\u0600-\u06FF]", text))

    if all_letters > 0 and english_letters / all_letters < 0.6:
        return False

    return True


async def correct_english(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if not text:
        return

    if not should_check(text):
        return

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=100
        )

        result = response.choices[0].message.content.strip()

        if result and result != "NO_CORRECTION":
            await update.message.reply_text(result)

    except Exception as e:
        print("Error:", e)


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set!")

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            correct_english
        )
    )

    print("English Correction Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
