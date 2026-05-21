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

# ================= READY =================

@bot.event
async def on_ready():

    print(f"🌸 Lisa Online: {bot.user}")

# ================= NEW MEMBER =================

@bot.event
async def on_member_join(member):

    print("NEW MEMBER JOINED")

    await handle_onboarding(member)

# ================= MESSAGE EVENT =================

@bot.event
async def on_message(message):

    print(
        f"MESSAGE RECEIVED: "
        f"{message.author} -> {message.content}"
    )

    if message.author.bot:
        return

    # ==========================================
    # DM PROCESSING
    # ==========================================

    if isinstance(message.channel, discord.DMChannel):

        print("DM DETECTED")

        try:

            await process_user_language(
                bot,
                message
            )

            print("DM PROCESS COMPLETE")

        except Exception as e:

            print("MAIN DM ERROR:", e)

        return

    # ==========================================
    # TRANSLATION SYSTEM
    # ==========================================

    try:

        await handle_translation(
            bot,
            message
        )

    except Exception as e:

        print("TRANSLATION ERROR:", e)

    # ==========================================
    # ADMIN COMMAND
    # ==========================================

    if (
        message.author.guild_permissions.administrator
        and message.content.lower()
        == "lisa setup language onboarding"
    ):

        print("STARTING ONBOARDING")

        await message.channel.send(
            "🌸 Starting onboarding..."
        )

        await auto_onboard_existing_members(
            message.guild
        )

        await message.channel.send(
            "🌸 Finished onboarding."
        )

        return

    await bot.process_commands(message)

# ================= HELP =================

@bot.command()
async def help(ctx):

    await ctx.send(
        "🌸 Lisa Multilingual Bot"
    )

# ================= START =================

bot.run(TOKEN)
