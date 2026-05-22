import discord
import asyncio

from database import (
    save_user,
    load_users
)

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

        already_configured = False

        # ======================================
        # DATABASE CHECK
        # ======================================

        if str(member.id) in users:
            already_configured = True

        # ======================================
        # ROLE CHECK
        # ======================================

        for role in member.roles:

            if role.name.lower() in LANGUAGE_ROLES:

                already_configured = True
                break

        # ======================================
        # SKIP CONFIGURED USERS
        # ======================================

        if already_configured:

            print(
                f"Skipping configured user: {member}"
            )

            return

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
# AUTO ONBOARD EXISTING MEMBERS
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

        content = message.content.strip()

        # ======================================
        # VALIDATE FORMAT
        # ======================================

        if (
            "Country:" not in content
            or "Language:" not in content
        ):

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
        # FIND MEMBER
        # ======================================

        guild = None
        member = None

        for g in bot.guilds:

            m = g.get_member(message.author.id)

            if m:

                guild = g
                member = m
                break

        if not guild or not member:

            await message.channel.send(
                "🌸 Could not find your server profile."
            )

            return

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
        # CREATE LANGUAGE ROLE
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
        # CREATE CATEGORY
        # ======================================

        category = discord.utils.get(
            guild.categories,
            name="🌍 Language Community"
        )

        if not category:

            category = await guild.create_category(
                "🌍 Language Community"
            )

        # ======================================
        # CREATE LANGUAGE CHANNEL
        # ======================================

        channel_name = language.lower()

        channel = discord.utils.get(
            guild.channels,
            name=channel_name
        )

        if not channel:

            overwrites = {

                guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),

                role:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True
                )
            }

            # ==================================
            # HIDE FROM ADMINS
            # ==================================

            for guild_role in guild.roles:

                if guild_role.permissions.administrator:

                    overwrites[guild_role] = (
                        discord.PermissionOverwrite(
                            view_channel=False
                        )
                    )

            channel = await guild.create_text_channel(

                channel_name,

                overwrites=overwrites,

                category=category,

                topic=f"{language} Viking Rise community"
            )

        # ======================================
        # REMOVE TRIBE CHAT ACCESS
        # ======================================

        tribe_chat = discord.utils.get(
            guild.channels,
            name="tribe-chat"
        )

        if tribe_chat:

            overwrite = (
                tribe_chat.overwrites_for(member)
            )

            overwrite.view_channel = False

            await tribe_chat.set_permissions(
                member,
                overwrite=overwrite
            )

        # ======================================
        # GIVE LANGUAGE ROLE
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
        # SUCCESS MESSAGE
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

        print(
            "PROCESS ERROR:",
            e
        )

        await message.channel.send(
            f"🌸 Error:\n{e}"
        )
