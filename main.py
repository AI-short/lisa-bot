"""
Lisa AI Discord Bot - FINAL FIXED VERSION
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
                            "You are Lisa, a smart AI Discord assistant. "
                            "You help server admins and users warmly."
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

        # ================= CREATE NORMAL CHANNEL =================

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

        # ================= CREATE PRIVATE ADMIN CHANNEL =================

        if "create admin channel" in text:

            guild = message.guild

            existing = discord.utils.get(
                guild.channels,
                name="lisa-admin"
            )

            if existing:

                await message.channel.send(
                    "🌸 lisa-admin already exists."
                )

                return

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=False
                )
            }

            for role in guild.roles:

                if role.permissions.administrator:

                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True
                    )

            await guild.create_text_channel(
                "lisa-admin",
                overwrites=overwrites
            )

            await message.channel.send(
                "🌸 Created private admin channel."
            )

            return

        # ================= LOCK CHANNEL =================

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

        # ================= UNLOCK CHANNEL =================

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

        # ================= AI ADMIN CHAT =================

        response = await ask_ai(
            f"""
            You are Lisa AI.

            Admin said:
            {message.content}

            Reply helpfully and briefly.
            """
        )

        await message.channel.send(response)

        return

    # =====================================================
    # USER AI CHAT
    # =====================================================

    if bot.user in message.mentions:

        cleaned = message.content.replace(
            f"<@{bot.user.id}>",
            ""
        ).strip()

        simple = cleaned.lower()

        # ================= SIMPLE FREE REPLIES =================

        if (
            "hello" in simple
            or "hi" in simple
            or "hey" in simple
        ):

            await message.reply(
                "🌸 Hello! How can I help you today?"
            )

            return

        if (
            "how are you" in simple
            or "how are u" in simple
        ):

            await message.reply(
                "🌸 I'm doing great! How about you?"
            )

            return

        if "who are you" in simple:

            await message.reply(
                "🌸 I'm Lisa, your AI Discord assistant!"
            )

            return

        if "thank" in simple:

            await message.reply(
                "🌸 You're welcome!"
            )

            return

        # ================= AI QUESTIONS =================

        response = await ask_ai(
            f"""
            You are Lisa AI.

            Reply warmly and helpfully.

            User said:
            {cleaned}
            """
        )

        await message.reply(response)

        return

    await bot.process_commands(message)

# ================= HELP COMMAND =================

@bot.command()
async def help(ctx):

    await ctx.send(
        "🌸 Lisa AI Commands\n\n"
        "Admins can say:\n"
        "Lisa create gaming channel\n"
        "Lisa create admin channel\n"
        "Lisa lock this channel\n"
        "Lisa unlock this channel"
    )

# ================= START =================

bot.run(TOKEN)
