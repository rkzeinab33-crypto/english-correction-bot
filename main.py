import os
import re
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from groq import Groq

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are a careful English correction assistant in a Telegram group.

Your ONLY task is to check the user's English message and correct genuine
English errors.

You MUST actively check EVERY message for:
- spelling mistakes
- grammar mistakes
- wrong verb forms
- wrong articles
- wrong prepositions
- incorrect singular/plural forms
- incorrect word choice
- unnatural or clearly incorrect phrasing

IMPORTANT:
Do NOT skip a message just because the mistake is small.

For example:
"I am agree with you."
-> "I agree with you."

"I didn't went there."
-> "I didn't go there."

"She don't like it."
-> "She doesn't like it."

"I realy like this movie."
-> "I really like this movie."

"I've listened to those music."
-> "I've listened to that music."

"I want to express my filling."
-> "I want to express my feelings."

However, DO NOT change correct natural English.

Do NOT rewrite a correct sentence to make it:
- more advanced
- more formal
- more elegant
- more native-like

Casual conversational English is completely acceptable.

Keep:
- the user's original meaning
- the user's tone
- the user's approximate English level
- emojis and casual style when appropriate

If there is ANY genuine grammar, spelling, or clearly incorrect
English problem, correct it.

If the entire message is correct and natural, respond with exactly:

NO_CORRECTION

If correction is needed:
- Return ONLY the corrected version.
- Do NOT explain the correction.
- Do NOT write "Correction:".
- Do NOT write "Why:".
- Do NOT use quotation marks.
- Do NOT add any extra comments.

IMPORTANT:
Do not invent mistakes.
Do not correct something merely because another phrasing is possible.
But do not ignore genuine mistakes, even small ones.
"""


def should_check(text):
    text = text.strip()

    if not text:
        return False

    # Ignore messages that are only URLs
    if re.fullmatch(r"https?://\S+", text):
        return False

    # Ignore messages with no English letters
    english_letters = len(re.findall(r"[A-Za-z]", text))

    if english_letters == 0:
        return False

    # Common short replies that normally don't need correction
    casual_replies = {
        "ok",
        "okay",
        "yeah",
        "yes",
        "no",
        "sure",
        "thanks",
        "thank you",
        "exactly",
        "of course",
        "me too",
        "me neither",
        "i think so",
        "that's good",
        "it's good",
        "sounds good",
        "that's great",
        "very good",
        "good idea",
        "i agree",
        "yeah i agree"
    }

    normalized = re.sub(r"[.!?,]+$", "", text.lower()).strip()

    if normalized in casual_replies:
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
            temperature=0.0,
            max_tokens=150
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
