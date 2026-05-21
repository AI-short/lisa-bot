"""
Lisa AI Discord Bot - GROQ Version
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

        return f"🌸 GROQ Error: {e}"

# ================= READY =================

@bot.event
async def on_ready():

    print(f"🌸 Lisa AI Online: {bot.user}")

# ================= MAIN =================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    text = message.content.lower()

    # ================= ADMIN COMMANDS =================

    if (
        message.author.guild_permissions.administrator
        and "lisa" in text
    ):

        # CREATE CHANNEL
        if "create" in text and "channel" in text:

            words = text.split()

            ignore = [
                "lisa",
                "create",
                "channel"
            ]

            for word in words:

                if word not in ignore:

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

        # CREATE PRIVATE ADMIN CHANNEL
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

        # AI ADMIN RESPONSE
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

    # ================= USER AI CHAT =================

    if bot.user in message.mentions:

        cleaned = message.content.replace(
            f"<@{bot.user.id}>",
            ""
        )

        # SIMPLE FREE REPLIES
        simple = cleaned.lower().strip()

        if "hello" in simple or "hi" in simple:

            await message.reply(
                "🌸 Hello! How can I help you today?"
            )

            return

        if "how are you" in simple:

            await message.reply(
                "🌸 I'm doing great!"
            )

            return

        if "who are you" in simple:

            await message.reply(
                "🌸 I'm Lisa, your AI Discord assistant!"
            )

            return

        # AI FOR COMPLEX QUESTIONS
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

# ================= COMMAND =================

@bot.command()
async def help(ctx):

    await ctx.send(
        "🌸 Lisa AI Commands\\n\\n"
        "Admins can say:\\n"
        "Lisa create gaming channel\\n"
        "Lisa create admin channel\\n"
        "Lisa lock this channel\\n"
        "Lisa unlock this channel"
    )

# ================= START =================

bot.run(TOKEN)
