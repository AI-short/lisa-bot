import discord
import asyncio

from database import save_user

async def handle_onboarding(member):

    try:

        dm = await member.create_dm()

        await dm.send(
            "🌸 Hello! I am Lisa.\n\n"
            "Please reply in this format:\n"
            "Country: YourCountry\n"
            "Language: YourLanguage"
        )

    except Exception as e:

        print("DM ERROR:", e)

async def auto_onboard_existing_members(guild):

    for member in guild.members:

        if member.bot:
            continue

        await handle_onboarding(member)

        await asyncio.sleep(1)

async def process_user_language(bot, message):

    content = message.content.lower()

    if "country:" not in content or "language:" not in content:
        return

    try:

        lines = content.split("\n")

        country = lines[0].replace("country:", "").strip().title()
        language = lines[1].replace("language:", "").strip().title()

        guild = bot.guilds[0]

        role = discord.utils.get(guild.roles, name=language)

        if not role:

            role = await guild.create_role(name=language)

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

        member = guild.get_member(message.author.id)

        await member.add_roles(role)

        save_user(
            str(member.id),
            country,
            language
        )

        await message.channel.send(
            f"🌸 Setup completed! You now have access to #{channel_name}"
        )

    except Exception as e:

        print("LANGUAGE SETUP ERROR:", e)
