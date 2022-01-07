import discord
from discord.ext import commands
from config import MOD_ID, RED, YELLOW
from utils.utils import pos_int, RelativeTime, format_time
import datetime as dt


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
        em.timestamp = dt.datetime.utcnow()
        await ctx.send(embed=em)

    @commands.command(aliases=["timeout"])
    @commands.has_role(MOD_ID)
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: commands.Greedy[RelativeTime] = None, *, reason = None):
        if duration is None:
            raise commands.BadArgument

        duration = dt.timedelta(minutes=sum(duration))
        duration_str = format_time(duration)
        duration = dt.datetime.utcnow() + duration
        dynamic_str = discord.utils.format_dt(duration.replace(tzinfo=dt.timezone.utc), "R")

        await member.edit(timeout_until=duration, reason=reason)

        em = discord.Embed(color=YELLOW, timestamp=dt.datetime.utcnow())
        em.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        em.description = f"{member.mention} has been timed out by {ctx.author.mention} for {duration_str}\n" \
                         f"Unmute: {dynamic_str}"
        await ctx.send(embed=em)

    @commands.command()
    @commands.has_role(MOD_ID)
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        await member.edit(timeout_until=None)

        em = discord.Embed(color=YELLOW, timestamp=dt.datetime.utcnow())
        em.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        em.description = f"{member.mention} has been ummuted"
        em.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Moderation(bot))
