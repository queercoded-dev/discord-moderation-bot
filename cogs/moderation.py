import discord
from discord.ext import commands
from config import MOD_ID, RED, YELLOW, LOG_ID
from cogs.logs import MODERATION
from utils.utils import pos_int, RelativeTime, format_time, utc_now
from utils.db_utils import insert_doc, find_docs, del_doc
import datetime as dt
from typing import Union
from random import randint
import re
from config import GREEN
from argparse import ArgumentParser, ArgumentTypeError

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


async def can_moderate_user(ctx: commands.Context, member: discord.Member):
    em = discord.Embed(color=RED, timestamp=utc_now())

    if member.bot:
        em.title = "🤖 You can't use this command on a bot"
        await ctx.send(embed=em)
        return False
    if ctx.author.id == member.id:
        em.title = "🤔 You can't use this command on yourself"
        await ctx.send(embed=em)
        return False
    if ctx.author.top_role <= member.top_role:
        em.title = "⛔ You do not have permission to use this command on that user"
        await ctx.send(embed=em)
        return False

    return True


class CmdArgParser(ArgumentParser):
    def __init__(self):
        super().__init__(allow_abbrev=False, exit_on_error=False, add_help=False)

    def error(self, message):
        raise commands.BadArgument


def bool_arg(value):
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    else:
        raise ArgumentTypeError


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: commands.Bot

    async def mod_action_embed(self, title=discord.Embed.Empty, desc=discord.Embed.Empty,
                               author: discord.Member = None, target: Union[discord.Member, discord.User] = None,
                               fields=None):
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
        await channel.send(embed=em)

    @commands.command()
    @commands.has_role(MOD_ID)
    async def purge(self, ctx: commands.Context, number: pos_int):
        """
        Purge messages in this channel
        """
        await ctx.channel.purge(limit=number + 1)  # +1 to account for the ctx message
        em = discord.Embed(colour=RED, description=f"{ctx.author.mention} purged {number} messages!")
        em.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
        em.timestamp = utc_now()
        await ctx.send(embed=em)

        # Log action
        await self.mod_action_embed(author=ctx.author, title="🔥 Purge",
                                    desc=f"{ctx.author.mention} purged {number} messages in {ctx.channel.mention}")

    @commands.command(aliases=["timeout"])
    @commands.has_role(MOD_ID)
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: commands.Greedy[RelativeTime] = None,
                   *, reason=None):
        """
        Bans a user for certain time-scale
        """
        if duration is None:
            raise commands.BadArgument

        if not await can_moderate_user(ctx, member):
            return

        duration = dt.timedelta(minutes=sum(duration))
        duration_str = format_time(duration)
        end_time = utc_now() + duration
        dynamic_str = discord.utils.format_dt(end_time, "R")

        await member.edit(timeout_until=end_time, reason=reason)
        case_num = await add_modlog(member, ctx.author, "timeout", reason, duration)

        em = discord.Embed(color=YELLOW, timestamp=utc_now())
        em.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        em.description = f"{member.mention} has been timed out by {ctx.author.mention} for {duration_str}\n" \
                         f"Unmute: {dynamic_str}"
        em.set_footer(text=f"Case #{case_num}")
        await ctx.send(embed=em)

        await self.mod_action_embed(author=ctx.author, target=member,
                                    desc=f"**🔇 Timed out {member.mention}**" +
                                         (f"**for**:\n```{reason}```" if reason else ""),
                                    fields={"Duration": duration_str, "Unmute": dynamic_str})

    @commands.command()
    @commands.has_role(MOD_ID)
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        """
        Unmute a user
        """
        if not await can_moderate_user(ctx, member):
            return

        await member.edit(timeout_until=None)

        em = discord.Embed(color=RED, timestamp=utc_now())
        em.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        em.description = f"{member.mention} has been ummuted"
        em.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=em)

        await self.mod_action_embed(author=ctx.author, target=member, title="🔊 Timeout removed")

    @commands.command()
    @commands.has_role(MOD_ID)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason):
        """
        Warn a user
        This adds an entry to the mod logs and dms the user the reason for the warning
        """
        if not await can_moderate_user(ctx, member):
            return

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
        await ctx.send(embed=em)

        await self.mod_action_embed(author=ctx.author, target=member,
                                    desc=f"**Warned {member.mention} for:**\n```{reason}```")

    @commands.command()
    @commands.has_role(MOD_ID)
    async def ban(self, ctx: commands.Context, user: Union[discord.Member, discord.User], *, reason=None):
        """
        Ban a user (currently only perma ban)
        """
        can_dm = True
        if isinstance(user, discord.Member):
            if not await can_moderate_user(ctx, user):
                return

            em = discord.Embed(color=RED, timestamp=utc_now())
            em.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            em.description = f"You have been banned for \n```{reason}```"
            try:
                await user.send(embed=em)
            except discord.Forbidden:
                can_dm = False
        else:  # discord.User
            can_dm = False

        await ctx.guild.ban(user, reason=reason)

        case_num = await add_modlog(user, ctx.author, "ban", reason)

        em = discord.Embed(color=RED, timestamp=utc_now())
        em.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        em.description = f"{user.mention} was banned by {ctx.author.mention}" + \
                         (f" for:\n```{reason}```" if reason else "")
        em.set_footer(text=f"Case #{case_num}" + " - Unable to dm user" if not can_dm else "")
        await ctx.send(embed=em)

        await self.mod_action_embed(author=ctx.author, target=user,
                                    desc=f"**Banned {user.mention}**" + (f" **for:**\n```{reason}```" if reason else "")
                                    )

    @commands.command()
    @commands.has_role(MOD_ID)
    async def unban(self, ctx: commands.Context, user: discord.User):
        """
        Unban a user
        """
        await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author.name}({ctx.author.id})")

        em = discord.Embed(color=RED, timestamp=utc_now())
        em.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        em.description = f"{user.mention} has been unbanned"
        em.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=em)

        await self.mod_action_embed(author=ctx.author, target=user, desc=f"👼 **Unbanned** {user.mention}")

    @commands.command()
    @commands.has_role(MOD_ID)
    async def modlogs(self, ctx: commands.Context, member: discord.Member):
        """
        View all mod log entries for the given member
        """
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

        await ctx.send(embed=em)

    @commands.command(aliases=["unwarn"])
    @commands.has_role(MOD_ID)
    async def removecase(self, ctx, member: discord.Member, case_number):
        """
        Remove a case by its case #
        """
        if not re.fullmatch(r"[0-9]{4}", case_number):
            raise commands.BadArgument

        case = await find_docs("mod_logs", {"case": case_number, "user": str(member.id)}, 1)

        if case:
            case = case[0]
        else:
            em = discord.Embed(colour=RED, title=f"🔍 Case #{case_number} not found", timestamp=utc_now())
            em.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            return await ctx.send(embed=em)

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
        await ctx.send(embed=em)

    @commands.command(aliases=["osem"])
    @commands.has_role(MOD_ID)
    async def embed(self, ctx, channel: discord.TextChannel, title, description, *args):
        """
        Quick embed t.osem <channel> "<title>" "<description>" *args*

        Args:
        --colour - The embed colour, defaults to mint green
        --timestamp True/False - Whether to add a timestamp, defaults to true
        --footer True/False - Whether to include the embed footer, defaults to true
        """
        parser = CmdArgParser()
        parser.add_argument("--colour", "-c", "--color")
        parser.add_argument("--timestamp", "-t", type=bool_arg, default=True)
        parser.add_argument("--footer", "-f", type=bool_arg, default=True)
        parsed = parser.parse_args(args)

        if parsed.colour:
            colour = await commands.ColourConverter().convert(ctx, parsed.colour)
        else:
            colour = GREEN

        title = str.strip(title)
        embed = discord.Embed(title=title, description=description, colour=colour)
        if parsed.footer:
            embed.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
        if parsed.timestamp:
            embed.timestamp = utc_now()
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Moderation(bot))
