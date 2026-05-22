import os
import discord
from discord.ext import commands

from onboarding import (
    auto_onboard_existing_members,
    process_user_language,
    handle_onboarding
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
# BOT READY
# ==========================================

@bot.event
async def on_ready():

    print(
        f"🌸 Lisa Online: {bot.user}"
    )

# ==========================================
# AUTO ONBOARD NEW MEMBERS
# ==========================================

@bot.event
async def on_member_join(member):

    await handle_onboarding(member)

# ==========================================
# MESSAGE EVENT
# ==========================================

@bot.event
async def on_message(message):

    # ======================================
    # IGNORE BOT ITSELF
    # ======================================

    if message.author == bot.user:
        return

    # ======================================
    # DM PROCESSING
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
    # SAFE ADMIN CHECK
    # ======================================

    is_admin = False

    if message.guild:

        is_admin = (
            message.author.guild_permissions
            .administrator
        )

    # ======================================
    # ADMIN COMMANDS
    # ======================================

    if is_admin:

        content = message.content.lower()

        # ==================================
        # START ONBOARDING
        # ==================================

        if (
            "lisa setup language onboarding"
            in content
        ):

            await message.channel.send(
                "🌸 Starting onboarding..."
            )

            await auto_onboard_existing_members(
                message.guild
            )

            await message.channel.send(
                "🌸 Onboarding completed."
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
    # PROCESS COMMANDS
    # ======================================

    await bot.process_commands(message)

# ==========================================
# RUN BOT
# ==========================================

bot.run(
    os.getenv("TOKEN")
)
