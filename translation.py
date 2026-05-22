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
# SEND WEBHOOK MESSAGE
# ==========================================

async def send_webhook_message(

    channel,

    content,

    username,

    avatar_url
):

    try:

        webhooks = await channel.webhooks()

        webhook = None

        for wh in webhooks:

            if wh.name == "Lisa Translation":

                webhook = wh
                break

        if not webhook:

            webhook = await channel.create_webhook(
                name="Lisa Translation"
            )

        await webhook.send(

            content=content,

            username=username,

            avatar_url=avatar_url
        )

    except Exception as e:

        print(
            "WEBHOOK ERROR:",
            e
        )

# ==========================================
# HANDLE TRANSLATION
# ==========================================

async def handle_translation(message):

    try:

        # ======================================
        # SAFETY CHECKS
        # ======================================

        if not message.guild:
            return

        if message.author.bot:
            return

        channel_name = (
            message.channel.name.lower()
        )

        print(
            f"Translation triggered -> "
            f"{channel_name}"
        )

        # ======================================
        # GET SOURCE LANGUAGE
        # ======================================

        source_language = channel_name

        if source_language == "tribe-chat":

            source_language = "english"

        source_code = LANGUAGE_MAP.get(
            source_language
        )

        if not source_code:
            return

        # ======================================
        # SEND TO TRIBE CHAT
        # ======================================

        tribe_chat = discord.utils.get(

            message.guild.text_channels,

            name="tribe-chat"
        )

        if (
            tribe_chat
            and channel_name != "tribe-chat"
        ):

            await send_webhook_message(

                tribe_chat,

                message.content,

                message.author.display_name,

                message.author.display_avatar.url
            )

        # ======================================
        # TRANSLATE TO OTHER CHANNELS
        # ======================================

        for target_language, target_code in LANGUAGE_MAP.items():

            target_channel = discord.utils.get(

                message.guild.text_channels,

                name=target_language
            )

            if not target_channel:
                continue

            # ==================================
            # SKIP SAME CHANNEL
            # ==================================

            if (
                target_channel.id
                == message.channel.id
            ):
                continue

            try:

                translated_text = await translate_text(

                    message.content,

                    target_code
                )

                await send_webhook_message(

                    target_channel,

                    translated_text,

                    message.author.display_name,

                    message.author.display_avatar.url
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
