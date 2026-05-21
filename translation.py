from deep_translator import GoogleTranslator
from langdetect import detect
import discord

# ==========================================
# TRANSLATION SYSTEM
# ==========================================

async def handle_translation(bot, message):

    # Ignore bots
    if message.author.bot:
        return

    # Ignore DMs
    if isinstance(message.channel, discord.DMChannel):
        return

    guild = message.guild

    # ==========================================
    # IGNORE GLOBAL CHANNELS
    # ==========================================

    ignored_channels = [
        "welcome",
        "rules",
        "announcements"
    ]

    if message.channel.name in ignored_channels:
        return

    # ==========================================
    # DETECT SOURCE LANGUAGE
    # ==========================================

    try:

        source_language = detect(
            message.content
        )

    except:
        return

    # ==========================================
    # TRANSLATE TO OTHER LANGUAGE CHANNELS
    # ==========================================

    for channel in guild.text_channels:

        # Skip same channel
        if channel.id == message.channel.id:
            continue

        # Skip ignored channels
        if channel.name in ignored_channels:
            continue

        # Skip non-language channels
        if channel.name in [
            "common",
            "general",
            "chat"
        ]:
            continue

        # ==========================================
        # AVOID ADMIN NOTIFICATION SPAM
        # ==========================================

        try:

            # Translate message
            translated_text = GoogleTranslator(
                source="auto",
                target=channel.name
            ).translate(message.content)

        except:
            continue

        # ==========================================
        # CREATE / GET WEBHOOK
        # ==========================================

        try:

            webhooks = await channel.webhooks()

            webhook = None

            for wh in webhooks:

                if wh.name == "Lisa Translator":

                    webhook = wh
                    break

            if webhook is None:

                webhook = await channel.create_webhook(
                    name="Lisa Translator"
                )

            # ==========================================
            # PREMIUM MESSAGE STYLE
            # ==========================================

            await webhook.send(

                content=translated_text,

                username=message.author.display_name,

                avatar_url=message.author.display_avatar.url,

                silent=True
            )

        except Exception as e:

            print(
                f"WEBHOOK ERROR: {e}"
            )
