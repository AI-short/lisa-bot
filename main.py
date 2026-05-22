import os
import discord

from discord.ext import commands

from onboarding import (
    handle_onboarding,
    process_user_language,
    auto_onboard_existing_members
)

from translation import (
    handle_translation
)

# ==========================================
# INTENTS
# ==========================================

intents = discord.Intents.default()

intents.message_content = True
intents.members = True
intents.guilds = True

# ==========================================
# BOT SETUP
# ==========================================

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ==========================================
# READY EVENT
# ==========================================

@bot.event
async def on_ready():

    print(
        f"🌸 Lisa Online: {bot.user}"
    )

    for guild in bot.guilds:

        await auto_onboard_existing_members(
            guild
        )

# ==========================================
# MEMBER JOIN
# ==========================================

@bot.event
async def on_member_join(member):

    await handle_onboarding(member)

# ==========================================
# MESSAGE EVENT
# ==========================================

@bot.event
async def on_message(message):

    channel_name = getattr(
        message.channel,
        "name",
        "DM"
    )

    print(
        f"Message received -> "
        f"{message.author} -> "
        f"{channel_name}"
    )

    # ======================================
    # IGNORE BOT MESSAGES
    # ======================================

    if message.author.bot:
        return

    # ======================================
    # DM ONBOARDING
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
    # TRANSLATION SYSTEM
    # ======================================

    await handle_translation(
        bot,
        message
    )

    # ======================================
    # COMMANDS
    # ======================================

    await bot.process_commands(
        message
    )

# ==========================================
# START BOT
# ==========================================

TOKEN = os.getenv("TOKEN")

bot.run(TOKEN)
