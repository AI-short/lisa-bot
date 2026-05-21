import discord
from discord.ext import commands
import asyncio

from config import TOKEN
from onboarding import handle_onboarding, auto_onboard_existing_members
from translation import handle_translation

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="lisa!",
    intents=intents,
    help_command=None
)

@bot.event
async def on_ready():

    print(f"🌸 Lisa Online: {bot.user}")

@bot.event
async def on_member_join(member):

    await handle_onboarding(member)

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    # Translation system
    await handle_translation(bot, message)

    # Admin setup command
    if (
        message.author.guild_permissions.administrator
        and message.content.lower() == "lisa setup language onboarding"
    ):

        await message.channel.send(
            "🌸 Starting onboarding for all members..."
        )

        await auto_onboard_existing_members(message.guild)

        await message.channel.send(
            "🌸 Finished onboarding process."
        )

    await bot.process_commands(message)

bot.run(TOKEN)
