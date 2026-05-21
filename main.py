import discord
from discord.ext import commands

from config import TOKEN

from onboarding import (
    handle_onboarding,
    auto_onboard_existing_members,
    process_user_language
)

from translation import handle_translation

# ================= DISCORD =================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="lisa!",
    intents=intents,
    help_command=None
)

# ================= READY EVENT =================

@bot.event
async def on_ready():

    print(f"🌸 Lisa Online: {bot.user}")

# ================= NEW MEMBER JOIN =================

@bot.event
async def on_member_join(member):

    await handle_onboarding(member)

# ================= MESSAGE EVENT =================

@bot.event
async def on_message(message):

    # Ignore bots
    if message.author.bot:
        return

    # =====================================================
    # DM LANGUAGE SETUP
    # =====================================================

    if isinstance(message.channel, discord.DMChannel):

        await process_user_language(bot, message)

        return

    # =====================================================
    # TRANSLATION SYSTEM
    # =====================================================

    await handle_translation(bot, message)

    # =====================================================
    # ADMIN SETUP COMMAND
    # =====================================================

    if (
        message.author.guild_permissions.administrator
        and message.content.lower()
        == "lisa setup language onboarding"
    ):

        await message.channel.send(
            "🌸 Starting onboarding for all members..."
        )

        await auto_onboard_existing_members(
            message.guild
        )

        await message.channel.send(
            "🌸 Finished onboarding process."
        )

        return

    await bot.process_commands(message)

# ================= HELP COMMAND =================

@bot.command()
async def help(ctx):

    await ctx.send(
        "🌸 Lisa Multilingual Commands\n\n"
        "Lisa setup language onboarding"
    )

# ================= START BOT =================

bot.run(TOKEN)
