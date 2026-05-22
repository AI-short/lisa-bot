import discord
import asyncio

from database import (
    save_user,
    load_users
)

# ==========================================
# DYNAMIC LANGUAGE ROLES
# ==========================================

LANGUAGE_ROLES = []

# ==========================================
# SEND ONBOARDING DM
# ==========================================

async def handle_onboarding(member):

    try:

        users = load_users()

        if str(member.id) in users:

            print(
                f"Skipping configured user: {member}"
            )

            return

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

        print(
            "DM ERROR:",
            e
        )

# ==========================================
# AUTO ONBOARD MEMBERS
# ==========================================

async def auto_onboard_existing_members(guild):

    for member in guild.members:

        if member.bot:
            continue

        await handle_onboarding(member)

        await asyncio.sleep(1)

# ==========================================
# PROCESS LANGUAGE
# ==========================================

async def process_user_language(bot, message):

    try:

        content = message.content.strip()

        if (
            "Country:" not in content
            or "Language:" not in content
        ):
            return

        lines = content.split("\n")

        if len(lines) < 2:
            return

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

            m = g.get_member(
                message.author.id
            )

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

            if role.name.lower() not in [
                "@everyone",
                "admin",
                "moderator",
                "lisa"
            ]:

                removable_roles.append(role)

        if removable_roles:

            try:

                await member.remove_roles(
                    *removable_roles
                )

            except Exception as e:

                print(
                    "ROLE REMOVE ERROR:",
                    e
                )

        # ======================================
        # FIND OR CREATE ROLE
        # ======================================

        role = discord.utils.get(
            guild.roles,
            name=language
        )

        if not role:

            try:

                role = await guild.create_role(
                    name=language
                )

                print(
                    f"Created role: {language}"
                )

            except Exception as e:

                print(
                    "ROLE CREATE ERROR:",
                    e
                )

                await message.channel.send(
                    "🌸 Could not create language role."
                )

                return

        # ======================================
        # FIND OR CREATE CATEGORY
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
        # FIND OR CREATE CHANNEL
        # ======================================

        channel_name = (
            language.lower()
            .replace(" ", "-")
        )

        channel = discord.utils.get(
            guild.text_channels,
            name=channel_name
        )

        if not channel:

            try:

                overwrites = {

                    guild.default_role:
                    discord.PermissionOverwrite(
                        view_channel=False
                    ),

                    role:
                    discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True
                    ),

                    guild.me:
                    discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True,
                        manage_webhooks=True
                    )
                }

                channel = await guild.create_text_channel(

                    name=channel_name,

                    overwrites=overwrites,

                    category=category
                )

                print(
                    f"Created channel: {channel_name}"
                )

            except Exception as e:

                print(
                    "CHANNEL CREATE ERROR:",
                    e
                )

        # ======================================
        # ASSIGN ROLE
        # ======================================

        try:

            await member.add_roles(role)

        except Exception as e:

            print(
                "ROLE ADD ERROR:",
                e
            )

            await message.channel.send(
                "🌸 Could not assign language role."
            )

            return

        # ======================================
        # SAVE USER
        # ======================================

        try:

            save_user(
                str(member.id),
                country,
                language
            )

        except Exception as e:

            print(
                "DATABASE SAVE ERROR:",
                e
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

        try:

            await message.channel.send(
                f"🌸 Error:\n{e}"
            )

        except:
            pass
