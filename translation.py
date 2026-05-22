import discord
from googletrans import Translator
import traceback

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

        print(
            f"Translation triggered -> "
            f"{message.channel.name} -> "
            f"{message.content}"
        )

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

        guild = message.guild

        if not guild:
            return

        source_channel = (
            message.channel.name.lower()
        )

        # ======================================
        # IGNORE SYSTEM CHANNELS
        # ======================================

        if source_channel in IGNORED_CHANNELS:
            return

        # ======================================
        # SOURCE LANGUAGE
        # ======================================

        source_lang = LANGUAGE_MAP.get(
            source_channel,
            "en"
        )

        # ======================================
        # LOOP CHANNELS
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
            # VALID TARGETS
            # ==================================

            if (
                target_channel != "tribe-chat"
                and
                target_channel
                not in LANGUAGE_MAP
            ):
                continue

            print(
                f"Sending to -> {target_channel}"
            )

            # ==================================
            # GET WEBHOOK
            # ==================================

            webhook = await get_webhook(
                channel
            )

            # ==================================
            # TRIBE CHAT
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

                print(
                    "Sent to tribe-chat"
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
            # TRANSLATE
            # ======================================

            translated = translator.translate(

                message.content,

                src=source_lang,

                dest=target_lang
            )

            # ======================================
            # SEND TRANSLATED
            # ======================================

            await webhook.send(

                content=translated.text,

                username=(
                    message.author.display_name
                ),

                avatar_url=(
                    message.author.display_avatar.url
                )
            )

            print(
                f"Translated sent -> "
                f"{target_channel}"
            )

    except Exception:

        print(
            "\n===== TRANSLATION ERROR =====\n"
        )

        traceback.print_exc()

        print(
            "\n=============================\n"
        )
