import discord
from discord.ext import commands
from config import MOD_ID, RED, YELLOW
from utils.utils import pos_int, RelativeTime, format_time, utc_now
from utils.db_utils import insert_doc, find_docs
import datetime as dt

EMBED_DESC_LIMIT = 4096


async def add_modlog(user_id: int, mod_id: int, log_type: str, reason: str, duration: dt.timedelta = None):
    if duration:
        duration = duration.total_seconds()

    data = {
        "user": user_id,
        "mod": mod_id,
        "type": log_type,
        "duration": duration,
        "reason": reason,
        "timestamp": utc_now(),
    }

    await insert_doc("mod_logs", data)


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


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: commands.Bot

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

    @commands.command(aliases=["timeout"])
    @commands.has_role(MOD_ID)
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: commands.Greedy[RelativeTime] = None,
                   *, reason=None):
        if duration is None:
            raise commands.BadArgument

        if not await can_moderate_user(ctx, member):
            return

        duration = dt.timedelta(minutes=sum(duration))
        duration_str = format_time(duration)
        end_time = utc_now() + duration
        dynamic_str = discord.utils.format_dt(end_time, "R")

        await member.edit(timeout_until=end_time, reason=reason)
        await add_modlog(member.id, ctx.author.id, "timeout", reason, duration)

        em = discord.Embed(color=YELLOW, timestamp=utc_now())
        em.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        em.description = f"{member.mention} has been timed out by {ctx.author.mention} for {duration_str}\n" \
                         f"Unmute: {dynamic_str}"
        await ctx.send(embed=em)

    @commands.command()
    @commands.has_role(MOD_ID)
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        if not await can_moderate_user(ctx, member):
            return

        await member.edit(timeout_until=None)

        em = discord.Embed(color=RED, timestamp=utc_now())
        em.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        em.description = f"{member.mention} has been ummuted"
        em.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=em)

    @commands.command()
    @commands.has_role(MOD_ID)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason):
        """
        Warn a user
        This adds an entry to the mod logs and dms the user the reason for the warning
        """
        if not await can_moderate_user(ctx, member):
            return

        await add_modlog(member.id, ctx.author.id, "warn", reason)

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
        if not can_dm:
            em.set_footer(text="Unable to DM that user")
        await ctx.send(embed=em)

    @commands.command()
    @commands.has_role(MOD_ID)
    async def modlogs(self, ctx: commands.Context, member: discord.Member):
        """
        View all mod log entries for the given member
        """
        entries = await find_docs("mod_logs", {"user": member.id})
        text = []
        for entry in entries:
            log_type = entry["type"].title()
            mod = await ctx.guild.try_member(entry["mod"])
            reason = entry["reason"]
            duration = dt.timedelta(seconds=entry["duration"]) if entry["duration"] else None
            timestamp = discord.utils.format_dt(entry["timestamp"])

            duration = f"**Duration:** {format_time(duration)}\n" if duration else ""  # Don't show if no duration

            text.append(f"**{log_type}**\n"
                        f"**Reason:** {reason}\n"
                        f"{duration}"
                        f"**Timestamp:** {timestamp}\n"
                        f"**Mod:** {mod.mention if mod else 'Unknown'}")

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


def setup(bot):
    bot.add_cog(Moderation(bot))
