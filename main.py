import os
import discord
from discord.ext import commands

from onboarding import (
    process_user_language,
    auto_onboard_existing_members
)

from translation import (
    handle_translation
)

# ======================================
# INTENTS
# ======================================

intents = discord.Intents.default()

intents.message_content = True
intents.members = True
intents.guilds = True

# ======================================
# BOT SETUP
# ======================================

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ======================================
# READY EVENT
# ======================================

@bot.event
async def on_ready():

    print(
        f"🌸 Lisa Online: {bot.user}"
    )

# ======================================
# MEMBER JOIN
# ======================================

@bot.event
async def on_member_join(member):

    await asyncio.sleep(2)

    await handle_onboarding(member)

# ======================================
# MESSAGE EVENT
# ======================================

@bot.event
async def on_message(message):

    # ======================================
    # IGNORE BOT MESSAGES
    # ======================================

    if message.author.bot:
        return

    # ======================================
    # LOG MESSAGE
    # ======================================

    try:

        if hasattr(
            message.channel,
            "name"
        ):

            print(
                f"Message received -> "
                f"{message.author} -> "
                f"{message.channel.name}"
            )

        else:

            print(
                f"Message received -> "
                f"{message.author} -> DM"
            )

    except:
        pass

    # ======================================
    # LANGUAGE ONBOARDING COMMAND
    # ======================================

    if (
        message.content.lower()
        == "lisa setup language onboarding"
    ):

        await auto_onboard_existing_members(
            message.guild
        )

        await message.channel.send(
            "🌸 Language onboarding started."
        )

        return

    # ======================================
    # PROCESS DM LANGUAGE SETUP
    # ======================================

    if isinstance(
        message.channel,
        discord.DMChannel
    ):

        await process_user_language(
            bot,
            message
        )

        return

    # ======================================
    # HANDLE TRANSLATIONS
    # ======================================

    await handle_translation(
        message
    )

    # ======================================
    # CONTINUE NORMAL COMMANDS
    # ======================================

    await bot.process_commands(
        message
    )

# ======================================
# RUN BOT
# ======================================

TOKEN = os.getenv(
    "DISCORD_TOKEN"
)

bot.run(TOKEN)
