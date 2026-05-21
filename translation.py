from deep_translator import GoogleTranslator
from langdetect import detect
import discord

async def handle_translation(bot, message):

    if isinstance(message.channel, discord.DMChannel):
        return

    try:

        detected_language = detect(message.content)

    except:

        return

    guild = message.guild

    for channel in guild.text_channels:

        if channel.name == message.channel.name:
            continue

        try:

            translated = GoogleTranslator(
                source='auto',
                target=channel.name
            ).translate(message.content)

            await channel.send(
                f"🌐 {message.author.display_name}: {translated}"
            )

        except:
            pass
