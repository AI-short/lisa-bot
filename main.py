
import os
import discord
from discord.ext import commands
import google.generativeai as genai
import asyncio

TOKEN = os.getenv("TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

genai.configure(api_key=GEMINI_KEY)

model = genai.GenerativeModel("gemini-2.0-flash")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="lisa!",
    intents=intents,
    help_command=None
)

async def ask_ai(prompt):
    try:
        response = await asyncio.to_thread(
            lambda: model.generate_content(prompt)
        )
        return response.text
    except Exception as e:
        print(e)
        return "🌸 AI is sleeping right now."

@bot.event
async def on_ready():
    print(f"🌸 Lisa AI Online: {bot.user}")

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    text = message.content.lower()

    # ADMIN AI COMMANDS
    if message.author.guild_permissions.administrator:

        if "lisa" in text:

            # CREATE CHANNEL
            if "create" in text and "channel" in text:

                words = text.split()

                for word in words:

                    if word not in [
                        "lisa",
                        "create",
                        "channel"
                    ]:

                        existing = discord.utils.get(
                            message.guild.channels,
                            name=word
                        )

                        if existing:

                            await message.channel.send(
                                f"🌸 #{word} already exists."
                            )

                            return

                        await message.guild.create_text_channel(word)

                        await message.channel.send(
                            f"🌸 Created #{word} channel."
                        )

                        return

            # LOCK CHANNEL
            if "lock this channel" in text:

                overwrite = message.channel.overwrites_for(
                    message.guild.default_role
                )

                overwrite.send_messages = False

                await message.channel.set_permissions(
                    message.guild.default_role,
                    overwrite=overwrite
                )

                await message.channel.send(
                    "🌸 Channel locked."
                )

                return

            # UNLOCK CHANNEL
            if "unlock this channel" in text:

                overwrite = message.channel.overwrites_for(
                    message.guild.default_role
                )

                overwrite.send_messages = True

                await message.channel.set_permissions(
                    message.guild.default_role,
                    overwrite=overwrite
                )

                await message.channel.send(
                    "🌸 Channel unlocked."
                )

                return

            # AI RESPONSE
            response = await ask_ai(
                f"""
                You are Lisa AI.
                Reply warmly and helpfully.

                Admin said:
                {message.content}
                """
            )

            await message.channel.send(response)

            return

    # USER AI CHAT
    if bot.user in message.mentions:

        cleaned = message.content.replace(
            f"<@{bot.user.id}>",
            ""
        )

        response = await ask_ai(
            f"""
            You are Lisa AI.
            Reply warmly and briefly.

            User said:
            {cleaned}
            """
        )

        await message.reply(response)

        return

    await bot.process_commands(message)

@bot.command()
async def help(ctx):

    await ctx.send(
        "🌸 Lisa AI Commands\\n\\n"
        "Admins can say:\\n"
        "Lisa create hindi channel\\n"
        "Lisa lock this channel\\n"
        "Lisa unlock this channel"
    )

bot.run(TOKEN)
