import os
import re
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from groq import Groq


BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set!")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set!")


client = Groq(api_key=GROQ_API_KEY)


SYSTEM_PROMPT = """
You are a STRICT English grammar and spelling correction assistant
for English learners in a casual Telegram group.

Your job is to carefully correct the user's English.

IMPORTANT:
You MUST check EVERY sentence in the message.
Do NOT check only the first sentence.
Do NOT stop after finding one mistake.

For EVERY sentence, carefully check:

1. Grammar
2. Verb forms
3. Verb tenses
4. Subject-verb agreement
5. Auxiliary verbs
6. Do/does/did structures
7. Present and past forms
8. Present perfect structures
9. Modal verbs
10. Articles (a/an/the)
11. Singular and plural nouns
12. Countable/uncountable nouns
13. Pronouns
14. Prepositions
15. Infinitive (to + verb)
16. Gerund (-ing)
17. Word order
18. Sentence structure
19. Incorrect word choice
20. Spelling
21. Missing or unnecessary words
22. Clearly unnatural English caused by a grammatical problem

Examples:

"I am agree with you."
→ "I agree with you."

"He go there yesterday."
→ "He went there yesterday."

"She don't like it."
→ "She doesn't like it."

"I didn't went there."
→ "I didn't go there."

"I have went there."
→ "I have been there."

"I realy like this movie."
→ "I really like this movie."

"I want to express my filling."
→ "I want to express my feelings."

"I've listened to those music."
→ "I've listened to that music."

IMPORTANT:
If a message contains multiple sentences, check ALL of them.

Example:

"I went to class yesterday. My teacher explain something important. I didn't understand it."

Correct version:

"I went to class yesterday. My teacher explained something important. I didn't understand it."

Do NOT leave a grammatical mistake just because another sentence is correct.

However:

DO NOT rewrite correct English just to make it more advanced.

DO NOT make simple English sound sophisticated.

DO NOT change the user's meaning.

DO NOT change the user's personality or tone.

DO NOT replace normal casual English with formal English.

For example, these are already acceptable:

"Me too."
"I think so."
"Sounds good."
"Yeah, exactly."
"That's great."
"I don't know."
"I'm gonna go."
"That's kinda funny."

Keep casual expressions when they are grammatically acceptable.

If the user's English is correct and natural, do not change it.

Preserve emojis and the user's casual style.

If the message contains NO genuine English mistakes, respond with EXACTLY:

NO_CORRECTION

If there is at least one mistake:

Return the COMPLETE corrected message.

Do NOT return only the corrected sentence.

Do NOT explain the mistakes.

Do NOT say "Correction:".

Do NOT say "Why:".

Do NOT list the mistakes.

Do NOT use quotation marks around the corrected message.

ONLY return the corrected message.

Before producing your answer, mentally check EVERY sentence one more time
to make sure you did not miss any grammar or spelling mistake.
"""


def should_check(text):
    text = text.strip()

    if not text:
        return False

    # Ignore URL-only messages
    if re.fullmatch(r"https?://\S+", text):
        return False

    # Must contain English letters
    english_letters = len(re.findall(r"[A-Za-z]", text))

    if english_letters == 0:
        return False

    # Very common short replies.
    # We ignore these to save API requests.
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

    normalized = re.sub(
        r"[.!?,]+$",
        "",
        text.lower()
    ).strip()

    if normalized in casual_replies:
        return False

    # Ignore messages that are mostly Persian/non-English
    all_letters = len(
        re.findall(r"[A-Za-z\u0600-\u06FF]", text)
    )

    if all_letters > 0:
        english_ratio = english_letters / all_letters

        if english_ratio < 0.6:
            return False

    return True


async def correct_english(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    if not text:
        return

    if not should_check(text):
        return

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",

            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": text
                }
            ],

            temperature=0,

            # Enough for normal group messages
            
        )

        result = response.choices[0].message.content.strip()

        if result and result != "NO_CORRECTION":

            await update.message.reply_text(
                result
            )

    except Exception as e:
        print("Error:", e)


def main():

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

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
