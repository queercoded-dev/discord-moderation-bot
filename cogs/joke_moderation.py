import discord
from discord.ext import commands
from config import MOD_ID, RED, YELLOW
from utils.utils import RelativeTime, format_time, utc_now
import datetime as dt
from typing import Union


class JokeModeration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: commands.Bot

    @commands.command(aliases=["timeout"])
    @commands.has_role(MOD_ID)
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: commands.Greedy[RelativeTime] = None,
                   *, reason=None):
        """
        Timeout a user for a given time period
        """
        if duration is None:
            raise commands.BadArgument

        duration = dt.timedelta(minutes=sum(duration))
        duration_str = format_time(duration)

        em = discord.Embed(color=YELLOW, timestamp=utc_now())
        em.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        em.description = f"{member.mention} has been timed out by {ctx.author.mention} for {duration_str}\n"
        await ctx.send(embed=em)

    @commands.command()
    @commands.has_role(MOD_ID)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason):
        """
        Warn a user
        """
        em = discord.Embed(color=RED, timestamp=utc_now())
        em.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        em.description = f"{member.mention} was warned by {ctx.author.mention} for:\n```{reason}```"
        await ctx.send(embed=em)

    @commands.command()
    @commands.has_role(MOD_ID)
    async def ban(self, ctx: commands.Context, user: Union[discord.Member, discord.User],
                  duration: commands.Greedy[RelativeTime], *, reason=None):
        """
        Ban a user
        """
        if duration:
            duration_delta = dt.timedelta(minutes=sum(duration))
            duration_str = format_time(duration_delta)
        else:
            # Mostly to satisfy IDEs
            duration_str = None

        em = discord.Embed(color=RED, timestamp=utc_now())
        em.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        em.description = f"{user.mention} was banned by {ctx.author.mention}" + \
                         (f" for:\n```{reason}```" if reason else "")
        if duration:
            em.add_field(name="Duration", value=duration_str)

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(JokeModeration(bot))
