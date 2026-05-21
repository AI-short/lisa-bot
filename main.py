"""
Lisa AI Discord Bot - FINAL STABLE VERSION
"""

import os
import discord
from discord.ext import commands
from groq import Groq
import asyncio

# ================= CONFIG =================

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(
    api_key=GROQ_API_KEY
)

# ================= DISCORD =================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="lisa!",
    intents=intents,
    help_command=None
)

# ================= AI =================

async def ask_ai(prompt):

    try:

        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are Lisa, a smart AI Discord assistant."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
        )

        return response.choices[0].message.content

    except Exception as e:

        print("GROQ ERROR:", e)

        return "🌸 Lisa AI is resting right now."

# ================= READY =================

@bot.event
async def on_ready():

    print(f"🌸 Lisa AI Online: {bot.user}")

# ================= MAIN =================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    text = message.content.lower().strip()

    # =====================================================
    # ADMIN COMMANDS
    # =====================================================

    if (
        message.author.guild_permissions.administrator
        and "lisa" in text
    ):

        # ================= CREATE CHANNEL =================

        if (
            "create" in text
            and "channel" in text
            and "admin" not in text
        ):

            words = text.split()

            ignore = [
                "lisa",
                "create",
                "channel"
            ]

            channel_name = None

            for word in words:

                if word not in ignore:

                    channel_name = word
                    break

            if not channel_name:

                await message.channel.send(
                    "🌸 Please give a channel name."
                )

                return

            existing = discord.utils.get(
                message.guild.channels,
                name=channel_name
            )

            if existing:

                await message.channel.send(
                    f"🌸 #{channel_name} already exists."
                )

                return

            await message.guild.create_text_channel(
                channel_name
            )

            await message.channel.send(
                f"🌸 Created #{channel_name} channel."
            )

            return

        # ================= DELETE CHANNEL =================

        if (
            "delete" in text
            and "channel" in text
        ):

            words = text.split()

            ignore = [
                "lisa",
                "delete",
                "channel"
            ]

            channel_name = None

            for word in words:
