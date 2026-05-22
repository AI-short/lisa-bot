import discord
from googletrans import Translator

translator = Translator()

# ==========================================
# LANGUAGE MAP
# ==========================================

LANGUAGE_MAP = {

    "english": "en",
    "hindi": "hi",
    "hinglish": "hi",
    "japanese": "ja",
    "spanish": "es",
    "french": "fr",
    "arabic": "ar",
    "german": "de",
    "russian": "ru"
}

# ==========================================
# TRANSLATE TEXT
# ==========================================

async def translate_text(text, dest):

    try:

        translated = translator.translate(
            text,
            dest=dest
        )

        return translated.text

    except Exception as e:

        print(
            "TRANSLATION ERROR:",
            e
        )

        return text

# ==========================================
# RELAY TO TRIBE CHAT
# ==========================================

async def relay_to_tribe_chat(message):

    try:

        guild = message.guild

        tribe_chat = discord.utils.get(
            guild.text_channels,
            name="tribe-chat"
        )

        if not tribe_chat:
            return

        # ======================================
        # CREATE WEBHOOK
        # ======================================

        webhooks = await tribe_chat.webhooks()

        webhook = None

        for wh in webhooks:

            if wh.name == "Lisa Relay":

                webhook = wh
                break

        if not webhook:

            webhook = await tribe_chat.create_webhook(
                name="Lisa Relay"
            )

        # ======================================
        # SEND MESSAGE
        # ======================================

        await webhook.send(

            content=message.content,

            username=message.author.display_name,

            avatar_url=message.author.display_avatar.url
        )

        print(
            f"Relayed message from "
            f"{message.author}"
        )

    except Exception as e:

        print(
            "TRIBE RELAY ERROR:",
            e
        )

# ==========================================
# HANDLE TRANSLATION
# ==========================================

async def handle_translation(message):

    try:

        if not message.guild:
            return

        if message.author.bot:
            return

        channel_name = (
            message.channel.name.lower()
        )

        # ======================================
        # SKIP TRIBE CHAT
        # ======================================

        if channel_name == "tribe-chat":
            return

        # ======================================
        # DETECT SOURCE LANGUAGE
        # ======================================

        source_language = channel_name

        source_code = LANGUAGE_MAP.get(
            source_language
        )

        if not source_code:
            return

        print(
            f"Translation triggered -> "
            f"{source_language}"
        )

        # ======================================
        # RELAY ORIGINAL MESSAGE
        # ======================================

        await relay_to_tribe_chat(
            message
        )

        # ======================================
        # TRANSLATE TO OTHER CHANNELS
        # ======================================

        for target_language, target_code in LANGUAGE_MAP.items():

            if target_language == source_language:
                continue

            target_channel = discord.utils.get(

                message.guild.text_channels,

                name=target_language
            )

            if not target_channel:
                continue

            try:

                translated_text = await translate_text(

                    message.content,

                    target_code
                )

                webhooks = await target_channel.webhooks()

                webhook = None

                for wh in webhooks:

                    if wh.name == "Lisa Translation":

                        webhook = wh
                        break

                if not webhook:

                    webhook = await target_channel.create_webhook(
                        name="Lisa Translation"
                    )

                await webhook.send(

                    content=translated_text,

                    username=message.author.display_name,

                    avatar_url=message.author.display_avatar.url
                )

                print(
                    f"Translated -> "
                    f"{target_language}"
                )

            except Exception as e:

                print(
                    "CHANNEL TRANSLATION ERROR:",
                    e
                )

    except Exception as e:

        print(
            "HANDLE TRANSLATION ERROR:",
            e
        )
