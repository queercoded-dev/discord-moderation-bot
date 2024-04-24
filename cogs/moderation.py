import discord
from discord.ext import commands, tasks
from config import RED, YELLOW, LOG_ID, GUILD_ID, APPEAL_URL
from cogs.logs import MODERATION
from utils.utils import format_time, utc_now
from utils.db_utils import insert_doc, find_docs, del_doc
import datetime as dt
from typing import Union
from random import randint
import re
from config import GREEN
from io import BytesIO

EMBED_DESC_LIMIT = 4096


async def add_modlog(user: Union[discord.Member, discord.User], mod: discord.Member, log_type: str, reason: str,
                     duration: dt.timedelta = None):
    if duration:
        duration = duration.total_seconds()

    case_num = str(randint(0, 9999)).zfill(4)

    data = {
        "case": case_num,
        "user": str(user.id),
        "mod": str(mod.id),
        "type": log_type,
        "duration": duration,
        "reason": reason,
        "timestamp": utc_now(),
    }
    await insert_doc("mod_logs", data)

    return case_num


async def can_moderate_user(ctx: discord.ApplicationContext, member: discord.Member):
    em = discord.Embed(color=RED, timestamp=utc_now())

    if member.bot:
        em.title = "🤖 You can't use this command on a bot"
        await ctx.respond(embed=em, ephemeral=True)
        return False
    if ctx.author.id == member.id:
        em.title = "🤔 You can't use this command on yourself"
        await ctx.respond(embed=em, ephemeral=True)
        return False
    if ctx.author.top_role <= member.top_role:
        em.title = "⛔ You do not have permission to use this command on that user"
        await ctx.respond(embed=em, ephemeral=True)
        return False

    return True


class OSEMmodal(discord.ui.Modal):
    def __init__(self, channel: discord.TextChannel, timestamp: bool):
        super().__init__(title="Embed Creation")

        self.target_channel = channel
        self.timestamp = timestamp

        self.add_item(
            discord.ui.InputText(label="Title", required=False)
        )
        self.add_item(
            discord.ui.InputText(label="Colour", required=False)
        )
        self.add_item(
            discord.ui.InputText(label="Description", required=False, style=discord.InputTextStyle.long)
        )

    async def callback(self, interaction: discord.Interaction):
        title = self.children[0].value
        colour = self.children[1].value
        desc = self.children[2].value

        if not title and not desc:
            await interaction.response.send_message("Either a title or description must be provided", ephemeral=True)
            return

        if colour:
            # ctx arg is unused so the type doesn't matter
            # noinspection PyTypeChecker
            colour = await commands.ColourConverter().convert(None, colour)
        else:
            colour = GREEN

        em = discord.Embed(title=title, description=desc, colour=colour)
        if self.timestamp:
            em.timestamp = discord.utils.utcnow()

        message = await self.target_channel.send(embed=em)

        await interaction.response.send_message(f"Sent -> {message.jump_url}", embed=em, ephemeral=True)


class EditEmbedModal(discord.ui.Modal):
    def __init__(self, message: discord.Message):
        super().__init__(title="Edit Embed")

        self.message = message

        self.add_item(
            discord.ui.InputText(label="Title", required=False)
        )
        self.add_item(
            discord.ui.InputText(label="Colour", required=False)
        )
        self.add_item(
            discord.ui.InputText(label="Description", required=False, style=discord.InputTextStyle.long)
        )

    async def callback(self, interaction: discord.Interaction):
        title = self.children[0].value
        colour = self.children[1].value
        desc = self.children[2].value

        if colour:
            # ctx arg is unused so the type doesn't matter
            # noinspection PyTypeChecker
            colour = await commands.ColourConverter().convert(None, colour)

        em = self.message.embeds[0]
        if title:
            em.title = title
        if desc:
            em.description = desc
        if colour:
            em.colour = colour

        message = await self.message.edit(embed=em)

        await interaction.response.send_message(f"Edited -> {message.jump_url}", embed=em, ephemeral=True)


async def reason_modal(ctx: discord.ApplicationContext, func):
    """
    This automatically prompts the user for a "reason" with the ReasonModal and passes that on to the inner function
    """
    modal = ReasonModal()

    async def callback(response: discord.Interaction):
        await func(response, modal.children[0].value)

    modal.callback = callback

    await ctx.send_modal(modal)


class ReasonModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Mod Action")

        self.add_item(
            discord.ui.InputText(label="Reason (Optional)", style=discord.InputTextStyle.long, required=False)
        )


def messages_to_file(messages: list[discord.Message]) -> discord.File:
    output = ""

    for message in messages[::-1]:
        output += f"{message.created_at.isoformat()} | {message.author} ({message.author.id})\n"

        content = []
        if message.embeds and message.embeds[0].type == "rich":
            content.append("[embed]")
        if message.attachments:
            content.append("[file]")
        if message.content:
            content.append(message.content)

        output += " | ".join(content) + "\n\n"

    file = BytesIO()

    file.write(output.encode())
    file.seek(0)

    return discord.File(file, filename="purged_messages.txt")


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: commands.Bot
        self.unban_loop.start()

    async def mod_action_embed(self, title=discord.Embed.Empty, desc=discord.Embed.Empty,
                               author: discord.Member = None, target: Union[discord.Member, discord.User] = None,
                               fields=None, file: discord.File = None):
        em = discord.Embed(colour=MODERATION, timestamp=utc_now(), title=title, description=desc)
        if author:
            em.set_footer(text=f"By {author.name}", icon_url=author.display_avatar.url)

        if target:
            em.set_author(name=target.display_name, icon_url=target.display_avatar.url)
            if not author:
                em.set_footer(text=f"User ID: {target.id}")

        if fields:
            for name, value in fields.items():
                em.add_field(name=name, value=value)

        channel = self.bot.get_channel(LOG_ID)
        await channel.send(embed=em, file=file)

    @discord.slash_command()
    @discord.default_permissions(manage_messages=True)
    async def purge(self, ctx: discord.ApplicationContext, count: int):
        """
        Purge messages in this channel
        """
        if count < 1:
            await ctx.respond("Count must be greater than 0", ephemeral=True)
            return

        messages = await ctx.channel.purge(limit=count + 1)  # +1 to account for the ctx message
        em = discord.Embed(colour=RED, description=f"{ctx.author.mention} purged {count} messages!")
        em.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
        em.timestamp = utc_now()
        await ctx.respond(embed=em)

        # Log action
        file = messages_to_file(messages)
        await self.mod_action_embed(author=ctx.author, title="🔥 Purge",
                                    desc=f"{ctx.author.mention} purged {count} messages in {ctx.channel.mention}",
                                    file=file)

    @discord.slash_command()
    @discord.default_permissions(moderate_members=True)
    @discord.option("units", description="The unit the duration is in", choices=[
        discord.OptionChoice(name="Minutes", value=60),
        discord.OptionChoice(name="Hours", value=60 * 60),
        discord.OptionChoice(name="Days", value=24 * 60 * 60),
    ])
    async def mute(self, ctx: discord.ApplicationContext, member: discord.Member,
                   raw_duration: discord.Option(int, "The duration of the mute", name="duration"), units: int):
        """
        Timeout a user for a given time period
        """
        if not await can_moderate_user(ctx, member):
            return

        if raw_duration < 1:
            await ctx.respond("Invalid duration", ephemeral=True)
            return

        async def callback(interaction, reason):
            # Combine unit/duration args
            duration = raw_duration * units
            duration = dt.timedelta(seconds=duration)

            if duration > dt.timedelta(days=28):
                await interaction.response.send_message("The max mute length is 28 days", ephemeral=True)
                return

            # Do stuff

            await interaction.response.defer()

            try:
                await member.timeout_for(duration, reason=reason)
            except discord.Forbidden:
                await interaction.followup.send("Unable to mute the user")
                return

            case_num = await add_modlog(member, ctx.author, "timeout", reason, duration)

            # Format duration

            duration_str = format_time(duration)
            end_time = utc_now() + duration
            dynamic_str = discord.utils.format_dt(end_time, "R")

            # Contact user

            em = discord.Embed(color=RED, timestamp=utc_now())
            em.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            em.description = f"You have been muted for {duration_str}\n```{reason}```"
            can_dm = True
            try:
                await member.send(embed=em)
            except discord.Forbidden:
                can_dm = False

            # Send response

            em = discord.Embed(color=YELLOW, timestamp=utc_now())
            em.set_author(name=member.display_name, icon_url=member.display_avatar.url)

            em.description = f"{member.mention} has been muted by {ctx.author.mention} for {duration_str}\n" \
                             f"Unmute: {dynamic_str}"

            em.set_footer(text=f"Case #{case_num}" + " - Unable to dm user" if not can_dm else "")
            await interaction.followup.send(embed=em)

            await self.mod_action_embed(author=ctx.author, target=member,
                                        desc=f"**🔇 Muted {member.mention}**" +
                                             (f" **for**:\n```{reason}```" if reason else ""),
                                        fields={"Duration": duration_str, "Unmute": dynamic_str})

        await reason_modal(ctx, callback)

    @discord.slash_command()
    @discord.default_permissions(moderate_members=True)
    async def unmute(self, ctx: discord.ApplicationContext, member: discord.Member):
        """
        Unmute a user
        """
        if not await can_moderate_user(ctx, member):
            return

        await ctx.defer()

        await member.timeout(None)

        em = discord.Embed(color=RED, timestamp=utc_now())
        em.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        em.description = f"{member.mention} has been ummuted"
        em.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.respond(embed=em)

        await self.mod_action_embed(author=ctx.author, target=member, title="🔊 Timeout removed")

    @discord.slash_command()
    @discord.default_permissions(manage_messages=True)
    async def warn(self, ctx: discord.ApplicationContext, member: discord.Member):
        """
        Warn a user
        """
        if not await can_moderate_user(ctx, member):
            return

        async def callback(interaction, reason):
            await interaction.response.defer()

            case_num = await add_modlog(member, ctx.author, "warn", reason)

            em = discord.Embed(color=RED, timestamp=utc_now())
            em.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            em.description = f"You have been warned for \n```{reason}```"
            can_dm = True
            try:
                await member.send(embed=em)
            except discord.Forbidden:
                can_dm = False

            em = discord.Embed(color=RED, timestamp=utc_now())
            em.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            em.description = f"{member.mention} was warned by {ctx.author.mention} for:\n```{reason}```"
            em.set_footer(text=f"Case #{case_num}" + " - Unable to dm user" if not can_dm else "")
            await ctx.followup.send(embed=em)

            await self.mod_action_embed(author=ctx.author, target=member,
                                        desc=f"**Warned {member.mention} for:**\n```{reason}```")

        await reason_modal(ctx, callback)

    @discord.slash_command()
    @discord.default_permissions(ban_members=True)
    @discord.option("units", description="The unit the duration is in", required=False, choices=[
        discord.OptionChoice(name="Minutes", value=60),
        discord.OptionChoice(name="Hours", value=60 * 60),
        discord.OptionChoice(name="Days", value=24 * 60 * 60),
    ])
    async def ban(self, ctx: discord.ApplicationContext, user: discord.User,
                  base_duration: discord.Option(int, name="duration", required=False), units: int):
        """
        Ban a user
        """
        member = ctx.guild.get_member(user.id)

        if base_duration and base_duration < 1:
            await ctx.respond("Invalid duration", ephemeral=True)
            return

        async def callback(interaction, reason):
            await interaction.response.defer()

            can_dm = True
            if member:
                if not await can_moderate_user(ctx, member):
                    return

                em = discord.Embed(color=RED, timestamp=utc_now())
                em.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
                em.description = f"You have been banned for \n```{reason}```"
                em.add_field(name="Appeal link", value=f"[Please click here to appeal this ban]({APPEAL_URL})",
                             inline=False)
                try:
                    await user.send(embed=em)
                except discord.Forbidden:
                    can_dm = False
            else:  # discord.User
                can_dm = False

            await ctx.guild.ban(user, reason=reason, delete_message_days=0)

            duration = base_duration * units if base_duration and units else None

            if duration:
                duration_delta = dt.timedelta(seconds=duration)
                end_time = utc_now() + duration_delta
                duration_str = format_time(duration_delta)
                dynamic_str = discord.utils.format_dt(end_time, "R")

                await insert_doc("pending", {
                    "user": str(user.id),
                    "timestamp": end_time,
                    "type": "ban",
                })
                self.unban_loop.start()
            else:
                # Mostly to satisfy IDEs
                duration_delta = None
                duration_str = None
                dynamic_str = None

            case_num = await add_modlog(user, ctx.author, "ban", reason, duration=duration_delta)

            em = discord.Embed(color=RED, timestamp=utc_now())
            em.set_author(name=user.display_name, icon_url=user.display_avatar.url)
            em.description = f"{user.mention} was banned by {ctx.author.mention}" + \
                             (f" for:\n```{reason}```" if reason else "")
            em.set_footer(text=f"Case #{case_num}" + " - Unable to dm user" if not can_dm else "")
            if duration:
                em.add_field(name="Duration", value=duration_str)

            await ctx.followup.send(embed=em)

            await self.mod_action_embed(author=ctx.author, target=user,
                                        desc=f"**Banned {user.mention}**" +
                                             (f" **for:**\n```{reason}```" if reason else ""),
                                        fields={"Duration": duration_str, "Unban": dynamic_str} if duration else None,
                                        )

        await reason_modal(ctx, callback)

    @discord.slash_command()
    @discord.default_permissions(ban_members=True)
    async def unban(self, ctx: discord.ApplicationContext, user: discord.User):
        """
        Unban a user
        """
        await ctx.defer()

        await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author.name}({ctx.author.id})")

        em = discord.Embed(color=RED, timestamp=utc_now())
        em.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        em.description = f"{user.mention} has been unbanned"
        em.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.respond(embed=em)

        await self.mod_action_embed(author=ctx.author, target=user, desc=f"👼 **Unbanned** {user.mention}")

    @discord.slash_command()
    @discord.default_permissions(manage_messages=True)
    async def modlogs(self, ctx: discord.ApplicationContext, member: discord.Member):
        """
        View all mod log entries for the given member
        """
        await ctx.defer()

        entries = await find_docs("mod_logs", {"user": str(member.id)})
        text = []
        for entry in entries:
            case_num = entry["case"]
            log_type = entry["type"].title()
            mod = entry["mod"]
            reason = entry["reason"]
            duration = dt.timedelta(seconds=entry["duration"]) if entry["duration"] else None
            timestamp = discord.utils.format_dt(entry["timestamp"])

            duration = f"**Duration:** {format_time(duration)}\n" if duration else ""  # Don't show if no duration

            text.append(f"**Case #{case_num}: {log_type}**\n"
                        f"**Reason:** {reason}\n"
                        f"{duration}"
                        f"**Timestamp:** {timestamp}\n"
                        f"**Mod:** <@{mod}>")

        em = discord.Embed(colour=RED, timestamp=utc_now(), description="")
        em.set_author(name=member.display_name, icon_url=member.display_avatar.url)

        # Go through the entries in reverse, to add as many entries as we can to the description
        for entry in text[::-1]:
            new = entry + "\n\n" + em.description
            if len(new) < EMBED_DESC_LIMIT:
                em.description = new
            else:
                break

        em.title = f"Mod Logs: {len(entries)} Entries"

        await ctx.respond(embed=em)

    @discord.slash_command()
    @discord.default_permissions(manage_messages=True)
    async def removecase(self, ctx: discord.ApplicationContext, member: discord.Member, case_number):
        """
        Remove a case by its case #
        """
        if not re.fullmatch(r"[0-9]{4}", case_number):
            raise commands.BadArgument

        await ctx.defer()

        case = await find_docs("mod_logs", {"case": case_number, "user": str(member.id)}, 1)

        if case:
            case = case[0]
        else:
            em = discord.Embed(colour=RED, title=f"🔍 Case #{case_number} not found", timestamp=utc_now())
            em.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            await ctx.respond(embed=em)
            return

        await del_doc(case["_id"], "mod_logs")

        log_type = case["type"]
        reason = case["reason"]
        timestamp = discord.utils.format_dt(case["timestamp"])
        mod = case["mod"]

        em = discord.Embed(colour=RED, timestamp=utc_now(), title=f"🗑️ Removed case #{case_number}")
        em.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        em.description = f"**{log_type.title()}**\n" \
                         f"**Reason:** {reason}\n" \
                         f"**Timestamp:** {timestamp}\n" \
                         f"**Mod:** <@{mod}>"
        await ctx.respond(embed=em)

    @discord.slash_command()
    @discord.default_permissions(manage_messages=True)
    @discord.option("timestamp", description="Whether to include a timestamp (default: false)", required=False,
                    choices=[
                        discord.OptionChoice(name="True", value=True),
                        discord.OptionChoice(name="False", value=False),
                    ])
    async def embed(self, ctx: discord.ApplicationContext, channel: discord.TextChannel, timestamp: bool = False):
        """
        Send a custom embed to a channel
        """
        await ctx.send_modal(OSEMmodal(channel, timestamp))

    @discord.slash_command()
    @discord.default_permissions(manage_messages=True)
    async def edit_embed(self, ctx: discord.ApplicationContext, message: discord.Message):
        """
        Alter an existing embed
        """
        await ctx.send_modal(EditEmbedModal(message))

    @discord.slash_command()
    @discord.default_permissions(manage_messages=True)
    async def addnote(self, ctx: discord.ApplicationContext, user: discord.User):
        """
        Add a note to the given user
        """

        async def callback(interaction, reason):
            await interaction.response.defer()
            await add_modlog(user, ctx.author, "note", reason)

            em = discord.Embed(color=RED, timestamp=utc_now())
            em.set_author(name=user.display_name, icon_url=user.display_avatar.url)
            em.description = f"Note added to {user.mention}:\n```{reason}```"
            await interaction.followup.send(embed=em)

        await reason_modal(ctx, callback)

    @tasks.loop(minutes=5)
    async def unban_loop(self):
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(GUILD_ID)

        # Get all pending bans
        pending_bans = await find_docs("pending", {"type": "ban"})

        for ban in pending_bans:
            _id = ban["_id"]
            user_id = int(ban["user"])
            timestamp: dt.datetime = ban["timestamp"]
            timestamp = timestamp.replace(tzinfo=dt.timezone.utc)

            if timestamp < utc_now():
                try:
                    await guild.unban(discord.Object(user_id), reason="Temp ban")
                except discord.NotFound:
                    # If the user is not banned, just delete the entry
                    # Could have been manually unbanned
                    pass

                await del_doc(_id, "pending")

        if not pending_bans:  # Don't bother running the loop if there are no bans
            self.unban_loop.stop()

    @discord.slash_command()
    @discord.default_permissions(ban_members=True)
    async def purgeuser(self, ctx: discord.ApplicationContext, user: discord.User, days: int = 1):
        """
        Purge a user's messages via a ban. The user will remain banned after this command is run
        This applies to all channels in the server
        Days must be between 1 and 7. Default is 1
        """
        if days < 1 or days > 7:
            await ctx.respond("`days` must be between 1 and 7", ephemeral=True)
            return

        await ctx.defer()

        await ctx.guild.ban(user, reason="Purge messages", delete_message_days=days)

        plural = f"{days} days" if days > 1 else "day"
        em = discord.Embed(colour=RED,
                           description=f"{ctx.author.mention} purged all messages by {user.mention} in the last {plural}",
                           timestamp=utc_now())
        em.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        await ctx.respond(embed=em)


def setup(bot):
    bot.add_cog(Moderation(bot))
