"""
Lisa - Smart Multilingual Discord Bot
"""

import asyncio
import json
import logging
import os
from pathlib import Path

import discord
from discord.ext import commands
from deep_translator import GoogleTranslator
from langdetect import detect as detect_lang

TOKEN = os.environ.get("TOKEN")
CATEGORY_NAME = "🌸 Lisa Translations"

LANG_TO_CHANNEL = {
    "en": "english",
    "es": "spanish",
    "fr": "french",
    "ar": "arabic",
    "hi": "hindi",
    "de": "german",
    "pt": "portuguese",
    "ru": "russian",
    "zh-cn": "chinese",
    "ja": "japanese",
    "ko": "korean",
    "it": "italian",
    "tr": "turkish",
    "ur": "urdu",
}

CHANNEL_TO_LANG = {v: k for k, v in LANG_TO_CHANNEL.items()}

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("lisa")

DATA_FILE = Path("lisa_users.json")

_user_data = {}
_lang_members = {}

def load_data():
    global _user_data, _lang_members

    if DATA_FILE.exists():
        try:
            raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            _user_data = raw.get("users", {})
            _lang_members = raw.get("lang_members", {})
        except Exception:
            log.warning("Could not load saved data")

def save_data():
    DATA_FILE.write_text(
        json.dumps({
            "users": _user_data,
            "lang_members": _lang_members
        }, indent=4),
        encoding="utf-8"
    )

def detect_language(text):
    try:
        code = detect_lang(text)
        return "zh-cn" if code.startswith("zh") else code
    except Exception:
        return None

async def translate_text(text, target):
    try:
        return await asyncio.to_thread(
            lambda: GoogleTranslator(source="auto", target=target).translate(text)
        )
    except Exception:
        return text

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="lisa!", intents=intents)

@bot.event
async def on_ready():
    load_data()
    print(f"🌸 Lisa is online as {bot.user}")

async def create_language_channel(guild, lang_code):
    channel_name = LANG_TO_CHANNEL.get(lang_code)

    if not channel_name:
        return None

    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)

    if not category:
        category = await guild.create_category(CATEGORY_NAME)

    channel = discord.utils.get(category.channels, name=channel_name)

    if not channel:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True
            )
        }

        channel = await guild.create_text_channel(
            channel_name,
            category=category,
            overwrites=overwrites
        )

    return channel

async def assign_language(member, lang_code):
    channel = await create_language_channel(member.guild, lang_code)

    if not channel:
        return None

    await channel.set_permissions(
        member,
        read_messages=True,
        send_messages=True
    )

    return channel

@bot.event
async def on_member_join(member):
    _user_data[str(member.id)] = {
        "step": "name"
    }

    save_data()

    system_channel = member.guild.system_channel

    if system_channel:
        await system_channel.send(
            f"Welcome {member.mention}! 🌸\n"
            "What is your name?"
        )

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)

    user = _user_data.get(uid)

    if user and user.get("step") == "name":
        user["name"] = message.content
        user["step"] = "country"

        save_data()

        await message.channel.send(
            f"Nice to meet you {message.content}! 🌸\n"
            "Which country are you from?"
        )

        return

    elif user and user.get("step") == "country":
        user["country"] = message.content
        user["step"] = "language"

        save_data()

        await message.channel.send(
            "What is your language?"
        )

        return

    elif user and user.get("step") == "language":
        language = message.content.lower().strip()

        lang_map = {
            "english": "en",
            "hindi": "hi",
            "spanish": "es",
            "french": "fr",
            "arabic": "ar",
            "german": "de",
            "portuguese": "pt",
            "russian": "ru",
            "chinese": "zh-cn",
            "japanese": "ja",
            "korean": "ko",
            "italian": "it",
            "turkish": "tr",
            "urdu": "ur"
        }

        lang_code = lang_map.get(language)

        if not lang_code:
            await message.channel.send(
                "Unsupported language. Try English, Hindi, French, Spanish, Arabic."
            )
            return

        user["language"] = lang_code
        user["step"] = "complete"

        save_data()

        channel = await assign_language(message.author, lang_code)

        if channel:
            await message.channel.send(
                f"🌸 Setup complete! Your language channel is #{channel.name}"
            )

        return

    category = discord.utils.get(message.guild.categories, name=CATEGORY_NAME)

    if category and message.channel.category == category:
        sender = message.author.display_name

        for channel in category.channels:
            target_lang = CHANNEL_TO_LANG.get(channel.name)

            if not target_lang:
                continue

            translated = await translate_text(message.content, target_lang)

            try:
                await channel.send(
                    f"**{sender}**: {translated}"
                )
            except Exception:
                pass

    await bot.process_commands(message)

@bot.command()
async def help(ctx):
    await ctx.send(
        "🌸 Lisa Commands\n"
        "lisa!help\n"
        "lisa!reset"
    )

@bot.command()
async def reset(ctx):
    _user_data[str(ctx.author.id)] = {
        "step": "name"
    }

    save_data()

    await ctx.send("🌸 Profile reset. What is your name?")

bot.run(TOKEN)
