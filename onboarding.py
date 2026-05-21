import discord
import asyncio

from database import (
    save_user,
    load_users
)

# ================= SEND ONBOARDING DM =================

async def handle_onboarding(member):

    try:

        dm = await member.create_dm()

        await dm.send(
            "🌸 Hello! I am Lisa.\n\n"
            "Please reply EXACTLY in this format:\n\n"
            "Country: India\n"
            "Language: Hindi"
        )

    except Exception as e:

        print("DM ERROR:", e)

# ================= ONBOARD EXISTING MEMBERS =================

async def auto_onboard_existing_members(guild):

    users = load_users()

    for member in guild.members:

        if member.bot:
            continue

        # Skip already configured users
        if str(member.id) in users:

            print(
                f"Skipping configured user: {member}"
            )

            continue

        await handle_onboarding(member)

        await asyncio.sleep(1)

# ================= PROCESS LANGUAGE SETUP =================

async def process_user_language(bot, message):

    try:

        content = message.content.strip()

        # Validate format
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

        guild = bot.guilds[0]

        member = guild.get_member(message.author.id)

        if not member:

            await message.channel.send(
                "🌸 Could not find your server profile."
            )

            return

        # ==========================================
        # REMOVE OLD LANGUAGE ROLES
        # ==========================================

        removable_roles = []

        for role in member.roles:

            if role.name.lower() in [
                "english",
                "hindi",
                "japanese",
                "spanish",
                "french",
                "arabic",
                "german",
                "russian"
            ]:

                removable_roles.append(role)

        if removable_roles:

            await member.remove_roles(
                *removable_roles
            )

        # ==========================================
        # CREATE ROLE IF MISSING
        # ==========================================

        role = discord.utils.get(
            guild.roles,
            name=language
        )

        if not role:

            role = await guild.create_role(
                name=language
            )

        # ==========================================
        # CREATE LANGUAGE CHANNEL IF MISSING
        # ==========================================

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
                overwrites=overwrites
            )

        # ==========================================
        # REMOVE COMMON CHANNEL ACCESS
        # ==========================================

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

        # ==========================================
        # GIVE LANGUAGE ROLE
        # ==========================================

        await member.add_roles(role)

        # ==========================================
        # SAVE USER DATA
        # ==========================================

        save_user(
            str(member.id),
            country,
            language
        )

        # ==========================================
        # SUCCESS MESSAGE
        # ==========================================

        await message.channel.send(
            f"🌸 Setup completed!\n\n"
            f"Country: {country}\n"
            f"Language: {language}\n\n"
            f"Your main channel is now "
            f"#{channel_name}"
        )

    except Exception as e:

        print("PROCESS ERROR:", e)

        await message.channel.send(
            f"🌸 Error: {e}"
        )
