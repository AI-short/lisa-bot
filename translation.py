import discord
from googletrans import Translator

translator = Translator()

# ==========================================
# LANGUAGE MAP
# ==========================================

LANGUAGE_MAP = {
    "english": "en",
    "hindi": "hi",
    "japanese": "ja",
    "spanish": "es",
    "french": "fr",
    "arabic": "ar",
    "german": "de",
    "russian": "ru"
}

# ==========================================
# IGNORED CHANNELS
# ==========================================

IGNORED_CHANNELS = [
    "welcome",
    "rules",
    "announcements",
    "redeem-codes",
    "clips-and-highlights"
]

# ==========================================
# GET OR CREATE WEBHOOK
# ==========================================

async def get_webhook(channel):

    webhooks = await channel.webhooks()

    for webhook in webhooks:

        if webhook.name == "Lisa Relay":

            return webhook

    return await channel.create_webhook(
        name="Lisa Relay"
    )

# ==========================================
# TRANSLATION SYSTEM
# ==========================================

async def handle_translation(bot, message):

    try:

        # ======================================
        # IGNORE BOTS
        # ======================================

        if message.author.bot:
            return

        # ======================================
        # IGNORE EMPTY
        # ======================================

        if not message.content.strip():
            return

        source_channel = (
            message.channel.name.lower()
        )

        # ======================================
        # IGNORE SYSTEM CHANNELS
        # ======================================

        if source_channel in IGNORED_CHANNELS:
            return

        guild = message.guild

        # ======================================
        # DETECT SOURCE LANGUAGE
        # ======================================

        source_lang = LANGUAGE_MAP.get(
            source_channel,
            "en"
        )

        # ======================================
        # TRANSLATE TO OTHER CHANNELS
        # ======================================

        for channel in guild.text_channels:

            target_channel = (
                channel.name.lower()
            )

            # ==================================
            # SKIP SAME CHANNEL
            # ==================================

            if target_channel == source_channel:
                continue

            # ==================================
            # SKIP SYSTEM CHANNELS
            # ==================================

            if target_channel in IGNORED_CHANNELS:
                continue

            # ==================================
            # SKIP INVALID CHANNELS
            # ==================================

            if (
                target_channel != "tribe-chat"
                and
                target_channel
                not in LANGUAGE_MAP
            ):
                continue

            # ==================================
            # CREATE WEBHOOK
            # ==================================

            webhook = await get_webhook(
                channel
            )

            # ==================================
            # SEND ORIGINAL TO TRIBE CHAT
            # ==================================

            if target_channel == "tribe-chat":

                if source_channel == "tribe-chat":
                    continue

                await webhook.send(

                    content=message.content,

                    username=(
                        message.author.display_name
                    ),

                    avatar_url=(
                        message.author.display_avatar.url
                    )
                )

                continue

            # ==================================
            # TARGET LANGUAGE
            # ==================================

            target_lang = LANGUAGE_MAP.get(
                target_channel
            )

            if not target_lang:
                continue

            # ==================================
            # TRANSLATE MESSAGE
            # ==================================

            translated = translator.translate(

                message.content,

                src=source_lang,

                dest=target_lang
            )

            # ==================================
            # SEND TRANSLATED MESSAGE
            # ==================================

            await webhook.send(

                content=translated.text,

                username=(
                    message.author.display_name
                ),

                avatar_url=(
                    message.author.display_avatar.url
                )
            )

    except Exception as e:

        print(
            "TRANSLATION ERROR:",
            e
        )
