import discord
import asyncio

from database import (
    save_user,
    load_users
)

# ==========================================
# ACTIVE ONBOARDING SESSIONS
# ==========================================

onboarding_sessions = {}

# ==========================================
# LANGUAGE ROLES
# ==========================================

LANGUAGE_ROLES = [
    "english",
    "hindi",
    "japanese",
    "spanish",
    "french",
    "arabic",
    "german",
    "russian"
]

# ==========================================
# SEND ONBOARDING DM
# ==========================================

async def handle_onboarding(member):

    try:

        users = load_users()

        # ======================================
        # SKIP CONFIGURED USERS
        # ======================================

        already_configured = False

        # Database check
        if str(member.id) in users:
            already_configured = True

        # Role check
        for role in member.roles:

            if role.name.lower() in LANGUAGE_ROLES:

                already_configured = True
                break

        if already_configured:

            print(
                f"Skipping configured user: {member}"
            )

            return

        # ======================================
        # STORE SESSION
        # ======================================

        onboarding_sessions[
            member.id
        ] = member.guild.id

        # ======================================
        # SEND DM
        # ======================================

        dm = await member.create_dm()

        await dm.send(
            "🌸 Hello! I am Lisa.\n\n"
            "Please reply EXACTLY in this format:\n\n"
            "Country: India\n"
            "Language: Hindi"
        )

        print(
            f"Onboarding DM sent to {member}"
        )

    except Exception as e:

        print("DM ERROR:", e)

# ==========================================
# ONBOARD EXISTING MEMBERS
# ==========================================

async def auto_onboard_existing_members(guild):

    for member in guild.members:

        if member.bot:
            continue

        await handle_onboarding(member)

        await asyncio.sleep(1)

# ==========================================
# PROCESS LANGUAGE SETUP
# ==========================================

async def process_user_language(bot, message):

    try:

        user_id = message.author.id

        # ======================================
        # CHECK SESSION
        # ======================================

        if user_id not in onboarding_sessions:

            await message.channel.send(
                "🌸 No active onboarding session found."
            )

            return

        guild_id = onboarding_sessions[user_id]

        guild = bot.get_guild(guild_id)

        if not guild:

            await message.channel.send(
                "🌸 Server not found."
            )

            return

        member = guild.get_member(user_id)

        if not member:

            await message.channel.send(
                "🌸 Could not find your server profile."
            )

            return

        content = message.content.strip()

        # ======================================
        # VALIDATE FORMAT
        # ======================================

        if (
            "Country:" not in content
            or "Language:" not in content
        ):

            await message.channel.send(
                "🌸 Invalid format.\n\n"
                "Use:\n"
                "Country: India\n"
                "Language: Hindi"
            )

            return

        lines = content.split("\n")

        country = (
            lines[0]
            .replace("Country:", "")
            .strip()
            .title()
        )

        language = (
            lines[1]
            .replace("Language:", "")
            .strip()
            .title()
        )

        # ======================================
        # REMOVE OLD LANGUAGE ROLES
        # ======================================

        removable_roles = []

        for role in member.roles:

            if role.name.lower() in LANGUAGE_ROLES:

                removable_roles.append(role)

        if removable_roles:

            await member.remove_roles(
                *removable_roles
            )

        # ======================================
        # CREATE ROLE IF MISSING
        # ======================================

        role = discord.utils.get(
            guild.roles,
            name=language
        )

        if not role:

            role = await guild.create_role(
                name=language
            )

        # ======================================
        # CREATE CHANNEL IF MISSING
        # ======================================

        channel_name = language.lower()

        channel = discord.utils.get(
            guild.channels,
            name=channel_name
        )

        if not channel:

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=False
                ),
                role: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True
                )
            }

            channel = await guild.create_text_channel(
                channel_name,
                overwrites=overwrites,
                topic=f"{language} Viking Rise community"
            )

        # ======================================
        # REMOVE COMMON ACCESS
        # ======================================

        common_channel = discord.utils.get(
            guild.channels,
            name="common"
        )

        if common_channel:

            overwrite = common_channel.overwrites_for(
                member
            )

            overwrite.view_channel = False

            await common_channel.set_permissions(
                member,
                overwrite=overwrite
            )

        # ======================================
        # GIVE ROLE
        # ======================================

        await member.add_roles(role)

        # ======================================
        # SAVE USER
        # ======================================

        save_user(
            str(member.id),
            country,
            language
        )

        # ======================================
        # REMOVE SESSION
        # ======================================

        if user_id in onboarding_sessions:

            del onboarding_sessions[user_id]

        # ======================================
        # SUCCESS RESPONSE
        # ======================================

        await message.channel.send(
            f"🌸 Setup completed successfully!\n\n"
            f"Country: {country}\n"
            f"Language: {language}\n\n"
            f"Your main communication channel is now:\n"
            f"#{channel_name}"
        )

        print(
            f"Setup completed for {member}"
        )

    except Exception as e:

        print("PROCESS ERROR:", e)

        await message.channel.send(
            f"🌸 Error:\n{e}"
        )
