"""
Lisa - Smart Multilingual Discord Bot
======================================
Requirements:
    pip install "discord.py>=2.3" "deep-translator>=1.11" "langdetect>=1.0.9" "google-generativeai>=0.5.0"
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
from google import genai

# ===================== CONFIGURATION =====================
TOKEN      = os.environ.get("TOKEN", "YOUR_TOKEN_HERE")
GEMINI_KEY = os.environ.get("GEMINI_KEY", "YOUR_GEMINI_KEY_HERE")

CATEGORY_NAME = "🌸 Lisa Translations"

LANG_TO_CHANNEL = {
    "en": "english", "es": "spanish", "fr": "french",
    "ar": "arabic",  "hi": "hindi",   "de": "german",
    "pt": "portuguese", "ru": "russian", "zh-cn": "chinese",
    "ja": "japanese", "ko": "korean", "it": "italian", "tr": "turkish",
}
CHANNEL_TO_LANG = {v: k for k, v in LANG_TO_CHANNEL.items()}

LANGUAGE_NAMES = {
    "hindi": "hi", "english": "en", "spanish": "es", "french": "fr",
    "arabic": "ar", "german": "de", "portuguese": "pt", "russian": "ru",
    "chinese": "zh-cn", "japanese": "ja", "korean": "ko",
    "italian": "it", "turkish": "tr", "urdu": "ur",
}
# =========================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("lisa")

# Setup Gemini AI
client = genai.Client(api_key=GEMINI_KEY)


DATA_FILE = Path("lisa_users.json")
_user_data:    dict[str, dict] = {}
_lang_members: dict[int, dict[str, set]] = {}
_server_config: dict[int, dict] = {}  # guild_id -> {channel_id: {translate: bool, access: bool}}
_admin_setup:   dict[int, dict] = {}  # guild_id -> {step, pending_channels}


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _load() -> None:
    global _user_data, _lang_members, _server_config, _admin_setup
    if DATA_FILE.exists():
        try:
            raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            _user_data     = raw.get("users", {})
            _lang_members  = {int(g): {l: set(m) for l, m in ls.items()} for g, ls in raw.get("lang_members", {}).items()}
            _server_config = {int(g): v for g, v in raw.get("server_config", {}).items()}
            _admin_setup   = {int(g): v for g, v in raw.get("admin_setup", {}).items()}
        except Exception:
            log.warning("Corrupt data – starting fresh.")


def _save() -> None:
    DATA_FILE.write_text(json.dumps({
        "users": _user_data,
        "lang_members": {str(g): {l: list(m) for l, m in ls.items()} for g, ls in _lang_members.items()},
        "server_config": {str(g): v for g, v in _server_config.items()},
        "admin_setup": {str(g): v for g, v in _admin_setup.items()},
    }, indent=4, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Gemini AI — Lisa's brain
# ---------------------------------------------------------------------------

async def lisa_think(prompt: str) -> str:
    """Ask Gemini a question and return the response."""
    try:
        system = (
            "You are Lisa, a warm and friendly multilingual Discord bot assistant. "
            "You speak naturally and helpfully. Keep responses short and clear. "
            "You help manage a Discord server with automatic translation features. "
            "When asked to do something, respond with a friendly confirmation. "
            "Never use technical jargon."
        )
        full_prompt = f"{system}\n\nUser: {prompt}"
        response = await asyncio.to_thread(
            lambda: client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt
            )
        )
        return response.text.strip()
    except Exception as e:
        log.error("Gemini error: %s", e)
        return "I'm thinking... please try again in a moment! 🌸"


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------

def _translate_sync(text: str, target: str) -> str:
    try:
        r = GoogleTranslator(source="auto", target=target).translate(text)
        return r if r else text
    except Exception as e:
        log.error("Translation error: %s", e)
        return text

async def translate(text: str, target: str) -> str:
    return await asyncio.to_thread(_translate_sync, text, target)

def detect_language(text: str) -> str | None:
    try:
        code = detect_lang(text)
        return "zh-cn" if code.startswith("zh") else code
    except Exception:
        return None

def resolve_language(tongue: str) -> str | None:
    tongue = tongue.strip().lower()
    return LANGUAGE_NAMES.get(tongue) or LANG_TO_CHANNEL.get(tongue)


# ---------------------------------------------------------------------------
# Channel management
# ---------------------------------------------------------------------------

async def get_or_create_lang_channel(guild: discord.Guild, lang_code: str) -> discord.TextChannel | None:
    ch_name  = LANG_TO_CHANNEL.get(lang_code)
    if not ch_name:
        return None
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if not category:
        try:
            category = await guild.create_category(CATEGORY_NAME)
        except discord.Forbidden:
            return None
    channel = discord.utils.get(category.channels, name=ch_name)
    if not channel:
        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_webhooks=True),
            }
            channel = await guild.create_text_channel(ch_name, category=category, overwrites=overwrites)
            log.info("Created #%s in %s", ch_name, guild.name)
        except discord.Forbidden:
            return None
    return channel


async def assign_channel(member: discord.Member, lang_code: str) -> discord.TextChannel | None:
    guild = member.guild
    gid   = guild.id
    uid   = str(member.id)

    old_lang = _user_data.get(uid, {}).get("lang_code")
    if old_lang and old_lang != lang_code:
        old_ch = discord.utils.get(guild.channels, name=LANG_TO_CHANNEL.get(old_lang, ""))
        if old_ch:
            await old_ch.set_permissions(member, overwrite=None)
        if gid in _lang_members:
            _lang_members[gid].get(old_lang, set()).discard(uid)

    channel = await get_or_create_lang_channel(guild, lang_code)
    if not channel:
        return None

    await channel.set_permissions(member, read_messages=True, send_messages=True)

    if gid not in _lang_members:
        _lang_members[gid] = {}
    if lang_code not in _lang_members[gid]:
        _lang_members[gid][lang_code] = set()
    _lang_members[gid][lang_code].add(uid)
    _save()
    return channel


async def cleanup_empty_channel(guild: discord.Guild, lang_code: str) -> None:
    if _lang_members.get(guild.id, {}).get(lang_code):
        return
    ch_name = LANG_TO_CHANNEL.get(lang_code)
    channel = discord.utils.get(guild.channels, name=ch_name) if ch_name else None
    if channel:
        try:
            await channel.delete(reason="No members left.")
            log.info("Deleted empty #%s", ch_name)
        except discord.Forbidden:
            pass


def _get_all_lang_channels(guild: discord.Guild) -> dict[str, discord.TextChannel]:
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if not category:
        return {}
    return {CHANNEL_TO_LANG[ch.name]: ch for ch in category.channels if ch.name in CHANNEL_TO_LANG}


# ---------------------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------------------

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="lisa!", intents=intents, help_command=None)


@bot.event
async def on_ready() -> None:
    _load()
    log.info("🌸 Lisa is online as %s", bot.user)


# ---------------------------------------------------------------------------
# Admin setup — Lisa DMs admin when joining a new server
# ---------------------------------------------------------------------------

@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    admin = guild.owner
    if not admin:
        return

    # Get all existing channels
    channels = [ch for ch in guild.text_channels]
    _admin_setup[guild.id] = {
        "step": "channel_setup",
        "pending": [ch.id for ch in channels],
        "current_index": 0,
        "config": {}
    }
    _save()

    try:
        await admin.send(
            f"Hello! 🌸 I'm **Lisa**, your multilingual translation bot!\n\n"
            f"I've joined **{guild.name}**. I'll now ask you about each channel so I know how to handle them.\n\n"
            "For each channel I'll ask:\n"
            "1. Should members have **access** to this channel?\n"
            "2. Should messages here be **translated** to language channels?\n\n"
            "Just reply naturally — I understand plain English! Let's begin..."
        )
        await asyncio.sleep(2)
        await ask_admin_about_channel(admin, guild)
    except discord.Forbidden:
        log.warning("Cannot DM admin of %s", guild.name)


async def ask_admin_about_channel(admin: discord.User, guild: discord.Guild) -> None:
    setup = _admin_setup.get(guild.id)
    if not setup:
        return

    pending = setup["pending"]
    index   = setup["current_index"]

    if index >= len(pending):
        # All channels configured
        await admin.send(
            "✅ All channels configured! Lisa is ready.\n\n"
            "Members who join will be onboarded in the common channel and then assigned their language channel automatically. 🌸"
        )
        _admin_setup.pop(guild.id, None)
        _save()
        return

    ch_id   = pending[index]
    channel = guild.get_channel(ch_id)
    if not channel:
        setup["current_index"] += 1
        await ask_admin_about_channel(admin, guild)
        return

    await admin.send(
        f"**#{channel.name}**\n"
        f"Should new members have **access** to this channel, and should messages here be **translated** to language channels?\n\n"
        f"_Example replies: 'yes to both', 'access yes translate no', 'no access but translate messages', 'skip'_"
    )


async def handle_admin_reply(message: discord.Message, guild: discord.Guild) -> None:
    setup = _admin_setup.get(guild.id)
    if not setup:
        return

    pending = setup["pending"]
    index   = setup["current_index"]

    if index >= len(pending):
        return

    ch_id   = pending[index]
    channel = guild.get_channel(ch_id)
    if not channel:
        return

    # Use Gemini to understand admin's reply
    prompt = (
        f"The admin was asked about Discord channel #{channel.name}. "
        f"They replied: '{message.content}'\n\n"
        "Extract two things:\n"
        "1. Should members have ACCESS to this channel? (yes/no)\n"
        "2. Should messages be TRANSLATED to language channels? (yes/no)\n\n"
        "Reply ONLY in this exact format:\n"
        "ACCESS: yes\nTRANSLATE: no"
    )

    response = await lisa_think(prompt)
    access    = "yes" in response.lower().split("access:")[-1].split("\n")[0].lower()
    translate = "yes" in response.lower().split("translate:")[-1].split("\n")[0].lower()

    setup["config"][str(ch_id)] = {"access": access, "translate": translate}
    setup["current_index"] += 1

    if guild.id not in _server_config:
        _server_config[guild.id] = {}
    _server_config[guild.id][str(ch_id)] = {"access": access, "translate": translate}
    _save()

    await message.channel.send(
        f"Got it! **#{channel.name}** → Access: {'✅' if access else '❌'} | Translate: {'✅' if translate else '❌'}\n"
    )
    await asyncio.sleep(1)
    await ask_admin_about_channel(message.author, guild)


# ---------------------------------------------------------------------------
# New member — onboard in common channel
# ---------------------------------------------------------------------------

@bot.event
async def on_member_join(member: discord.Member) -> None:
    uid = str(member.id)
    gid = member.guild.id

    _user_data[uid] = {
        "step": "awaiting_name",
        "name": "", "country": "", "lang_code": "",
        "guild_id": gid
    }
    _save()

    # Find common channel (first accessible channel not in Lisa category)
    category = discord.utils.get(member.guild.categories, name=CATEGORY_NAME)
    lisa_ids  = {c.id for c in category.channels} if category else set()

    # Find channel marked as accessible in server config
    config    = _server_config.get(gid, {})
    common_ch = None
    for ch in member.guild.text_channels:
        if ch.id in lisa_ids:
            continue
        ch_cfg = config.get(str(ch.id), {})
        if ch_cfg.get("access", True):
            common_ch = ch
            break

    if not common_ch:
        common_ch = member.guild.system_channel or next(
            (c for c in member.guild.text_channels if c.id not in lisa_ids), None
        )

    if common_ch:
        # Give access to common channel only
        await common_ch.set_permissions(member, read_messages=True, send_messages=True)
        await common_ch.send(
            f"Welcome {member.mention}! 🌸 I'm **Lisa** — your multilingual companion!\n"
            f"I'll help you connect with everyone in your own language.\n"
            f"Let's get started! What is your **name**?"
        )

    # Also DM them
    try:
        await member.send(
            f"Hello {member.mention}! 🌸 Welcome to **{member.guild.name}**!\n"
            "I'm Lisa — I'll make sure you can chat with everyone in your own language. "
            "Please reply to my message in the server to get set up!"
        )
    except discord.Forbidden:
        pass


# ---------------------------------------------------------------------------
# Member leave
# ---------------------------------------------------------------------------

@bot.event
async def on_member_remove(member: discord.Member) -> None:
    uid  = str(member.id)
    lang = _user_data.get(uid, {}).get("lang_code")
    gid  = member.guild.id
    if lang and gid in _lang_members:
        _lang_members[gid].get(lang, set()).discard(uid)
        await cleanup_empty_channel(member.guild, lang)
    _user_data.pop(uid, None)
    _save()


# ---------------------------------------------------------------------------
# Main message handler
# ---------------------------------------------------------------------------

@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    # Handle DMs — check if admin is in setup flow
    if isinstance(message.channel, discord.DMChannel):
        # Check if this user is an admin doing setup
        for guild in bot.guilds:
            if guild.owner_id == message.author.id and guild.id in _admin_setup:
                await handle_admin_reply(message, guild)
                return
        await handle_dm(message)
        return

    uid  = str(message.author.id)
    user = _user_data.get(uid, {})

    # Handle @mentions of Lisa
    if bot.user in message.mentions:
        response = await lisa_think(
            f"A Discord user named {message.author.display_name} said to you: '{message.content}'. "
            "Respond warmly and helpfully as Lisa the translation bot."
        )
        await message.reply(response, mention_author=False)
        return

    # Onboarding in server channel
    if user.get("step") not in ("complete", "") and user.get("step") is not None:
        await handle_server_onboarding(message, user)
        return

    # Auto detect language for non-onboarded users
    if user.get("step") != "complete" and message.guild:
        detected = detect_language(message.content)
        if detected and detected in LANG_TO_CHANNEL:
            _user_data[uid] = {
                "step": "complete",
                "name": message.author.display_name,
                "country": "Unknown",
                "lang_code": detected,
                "guild_id": message.guild.id,
            }
            member = message.guild.get_member(message.author.id)
            if member:
                await assign_channel(member, detected)
                # Remove access from common channels
                await remove_common_access(member)
            _save()

    # Translation inside Lisa language channels
    if message.guild:
        category = discord.utils.get(message.guild.categories, name=CATEGORY_NAME)
        if category and message.channel.category_id == category.id:
            sender_name  = user.get("name") or message.author.display_name
            all_channels = _get_all_lang_channels(message.guild)

            try:
                await message.delete()
            except discord.Forbidden:
                pass

            tasks = [
                _send_translation(message.content, sender_name, lang, ch)
                for lang, ch in all_channels.items()
            ]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            return

        # Translate messages from configured channels
        gid    = message.guild.id
        config = _server_config.get(gid, {})
        ch_cfg = config.get(str(message.channel.id), {})
        if ch_cfg.get("translate", False):
            sender_name  = user.get("name") or message.author.display_name
            all_channels = _get_all_lang_channels(message.guild)
            tasks = [
                _send_translation(message.content, sender_name, lang, ch)
                for lang, ch in all_channels.items()
            ]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    await bot.process_commands(message)


async def remove_common_access(member: discord.Member) -> None:
    """Remove member's access from all non-Lisa channels."""
    gid    = member.guild.id
    config = _server_config.get(gid, {})
    category = discord.utils.get(member.guild.categories, name=CATEGORY_NAME)
    lisa_ids = {c.id for c in category.channels} if category else set()

    for ch in member.guild.text_channels:
        if ch.id in lisa_ids:
            continue
        try:
            await ch.set_permissions(member, read_messages=False)
        except discord.Forbidden:
            pass


async def handle_server_onboarding(message: discord.Message, user: dict) -> None:
    uid  = str(message.author.id)
    step = user.get("step")

    if step == "awaiting_name":
        user["name"] = message.content.strip()
        user["step"] = "awaiting_country"
        _save()
        await message.channel.send(
            f"Nice to meet you, **{user['name']}**! 🌸\n"
            f"Which **country** are you from?"
        )

    elif step == "awaiting_country":
        user["country"] = message.content.strip()
        user["step"]    = "awaiting_language"
        _save()
        await message.channel.send(
            f"Great, you're from **{user['country']}**! 🌸\n"
            "What is your **mother tongue** (native language)?\n"
            "_Example: Hindi, French, Spanish, Arabic, English..._"
        )

    elif step == "awaiting_language":
        tongue    = message.content.strip()
        lang_code = resolve_language(tongue)

        if not lang_code:
            # Try Gemini to understand the language name
            prompt   = f"What is the ISO 639-1 language code for '{tongue}'? Reply with ONLY the 2-letter code, nothing else."
            response = await lisa_think(prompt)
            lang_code = response.strip().lower()[:5]
            if lang_code not in LANG_TO_CHANNEL:
                lang_code = None

        if not lang_code:
            await message.channel.send(
                f"Hmm, I don't recognize **{tongue}** yet. 🌸\n"
                "Please try: Hindi, French, Spanish, Arabic, English, German, Portuguese, Russian, Chinese, Japanese, Korean, Italian, Turkish"
            )
            return

        user["lang_code"] = lang_code
        user["step"]      = "complete"
        _save()

        member  = message.guild.get_member(message.author.id)
        channel = await assign_channel(member, lang_code)

        # Remove access from common channels
        await remove_common_access(member)

        ch_name = LANG_TO_CHANNEL.get(lang_code, lang_code)
        await message.channel.send(
            f"You're all set, **{user['name']}**! 🌸\n"
            f"I've given you access to **#{ch_name}**.\n"
            "All messages from other members will be translated into your language there. "
            "Just write in your language — everyone will understand you! 🎉"
        )


async def handle_dm(message: discord.Message) -> None:
    uid  = str(message.author.id)
    user = _user_data.get(uid)

    if not user:
        response = await lisa_think(f"Someone DMed you saying: '{message.content}'. Respond as Lisa the Discord translation bot.")
        await message.channel.send(response)
        return

    if user.get("step") == "complete":
        response = await lisa_think(
            f"A user named {user.get('name', 'friend')} DMed you: '{message.content}'. "
            "Respond helpfully as Lisa the translation bot. Keep it short."
        )
        await message.channel.send(response)


async def _send_translation(text: str, sender_name: str, target_lang: str, channel: discord.TextChannel) -> None:
    translated = await translate(text, target_lang)
    try:
        await channel.send(
            f"**{sender_name}** — {translated}",
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except discord.HTTPException as e:
        log.error("Send failed to #%s: %s", channel.name, e)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@bot.command(name="lisa_help")
async def help_cmd(ctx: commands.Context) -> None:
    await ctx.send(
        "**Lisa Commands** 🌸\n"
        "`lisa!help` — show this message\n"
        "`lisa!profile` — view your profile\n"
        "`lisa!reset` — reset your profile\n"
        "`lisa!mylang` — check your language channel\n"
        "`lisa!setup` — admin: redo channel setup\n\n"
        "Just talk to me naturally — I understand plain English! 🌸"
    )


@bot.command(name="profile")
async def profile(ctx: commands.Context) -> None:
    uid  = str(ctx.author.id)
    user = _user_data.get(uid)
    if not user or user.get("step") != "complete":
        await ctx.send("You haven't finished setup yet. 🌸")
        return
    ch_name = LANG_TO_CHANNEL.get(user["lang_code"], user["lang_code"])
    await ctx.send(
        f"**Your Lisa Profile** 🌸\n"
        f"Name: {user['name']}\n"
        f"Country: {user['country']}\n"
        f"Language Channel: #{ch_name}"
    )


@bot.command(name="mylang")
async def mylang(ctx: commands.Context) -> None:
    uid  = str(ctx.author.id)
    user = _user_data.get(uid)
    if not user or not user.get("lang_code"):
        await ctx.send("You haven't been assigned a language channel yet. 🌸")
        return
    ch_name = LANG_TO_CHANNEL.get(user["lang_code"], user["lang_code"])
    await ctx.send(f"Your language channel is **#{ch_name}** 🌸")


@bot.command(name="reset")
async def reset(ctx: commands.Context) -> None:
    uid  = str(ctx.author.id)
    lang = _user_data.get(uid, {}).get("lang_code")
    gid  = ctx.guild.id if ctx.guild else None
    if lang and gid and gid in _lang_members:
        _lang_members[gid].get(lang, set()).discard(uid)
        if ctx.guild:
            await cleanup_empty_channel(ctx.guild, lang)
    _user_data[uid] = {"step": "awaiting_name", "name": "", "country": "", "lang_code": "", "guild_id": gid}
    _save()
    await ctx.send("Profile reset! What is your **name**? 🌸")


@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def setup_cmd(ctx: commands.Context) -> None:
    """Admin only: redo the channel setup."""
    guild = ctx.guild
    channels = [ch for ch in guild.text_channels]
    _admin_setup[guild.id] = {
        "step": "channel_setup",
        "pending": [ch.id for ch in channels],
        "current_index": 0,
        "config": {}
    }
    _save()
    try:
        await ctx.author.send(
            "Let's redo the channel setup! 🌸\n"
            "I'll ask you about each channel one by one..."
        )
        await ask_admin_about_channel(ctx.author, guild)
        await ctx.send("Check your DMs! I've started the setup process. 🌸")
    except discord.Forbidden:
        await ctx.send("I couldn't DM you. Please enable DMs from server members.")


# ---------------------------------------------------------------------------
# Onboard existing members
# ---------------------------------------------------------------------------

@bot.command(name="onboard")
@commands.has_permissions(administrator=True)
async def onboard_all(ctx: commands.Context) -> None:
    """Admin only: lisa!onboard — greets all existing members who haven't been set up yet."""
    guild   = ctx.guild
    count   = 0

    # Find common channel
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    lisa_ids  = {c.id for c in category.channels} if category else set()
    common_ch = next(
        (c for c in guild.text_channels if c.id not in lisa_ids), None
    )

    for member in guild.members:
        if member.bot:
            continue
        uid  = str(member.id)
        user = _user_data.get(uid, {})
        if user.get("step") == "complete":
            continue  # Already onboarded

        # Register them
        _user_data[uid] = {
            "step": "awaiting_name",
            "name": "", "country": "", "lang_code": "",
            "guild_id": guild.id
        }
        count += 1

        # DM them
        try:
            await member.send(
                f"Hello {member.mention}! 🌸 I'm **Lisa** — your multilingual companion on **{guild.name}**!\n"
                "I help everyone chat in their own language.\n"
                f"Please go to **#{common_ch.name}** and tell me your name to get started!"
            )
        except discord.Forbidden:
            pass

        # Give access to common channel
        if common_ch:
            try:
                await common_ch.set_permissions(member, read_messages=True, send_messages=True)
            except discord.Forbidden:
                pass

        await asyncio.sleep(0.5)  # Avoid rate limits

    _save()
    await ctx.send(
        f"🌸 Done! Sent onboarding messages to **{count}** members.\n"
        "They will be asked for their name, country and language in the common channel."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    bot.run(TOKEN, log_handler=None)
