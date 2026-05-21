import discord
from discord.ext import commands

from onboarding import (
    auto_onboard_existing_members,
    process_user_language
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

# ==========================================
# BOT
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

# ==========================================
# MEMBER JOIN
# ==========================================

@bot.event
async def on_member_join(member):

    await process_user_language(
        bot,
        member
    )

# ==========================================
# MESSAGE EVENT
# ==========================================

@bot.event
async def on_message(message):

    # Ignore self
    if message.author == bot.user:
        return

    # ======================================
    # SAFE ADMIN CHECK
    # ======================================

    is_admin = (
        message.guild
        and
        message.author.guild_permissions
        .administrator
    )

    # ======================================
    # DM HANDLING
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
    # ADMIN COMMANDS
    # ======================================

    if is_admin:

        content = message.content.lower()

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
    # TRANSLATION
    # ======================================

    await handle_translation(
        bot,
        message
    )

    await bot.process_commands(message)
