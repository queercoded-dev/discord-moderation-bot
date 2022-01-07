import discord
from discord.ext import commands
from config import LOG_ID, RED, GUILD_ID
import datetime as dt
import traceback as tb
from math import ceil

from utils import format_time

EDIT = 0xffca3a  # yellow
DELETE = 0xff595e  # red
JOIN = 0x8ac926  # green
LEAVE = 0x1982c4  # blue
ROLE = 0xEE6F3D  # orange
NICKNAME = 0x6a4c93  # purple
VOICE = 0x99e5da  # aqua ish


def _crop(text: str, chars=2000, border="--Snippet--"):
    """
    Crop text to a certain character length based on word borders
    """
    if len(text) > chars:
        text = text[:chars - len(border)]  # initial crop, just get the character count right
        text = " ".join(text.split(" ")[:-1])  # cut off at nearest word boundary
        text += border  # append border to signify cut off
    return text


async def error_embed(ctx: commands.Context, error: str):
    em = discord.Embed(colour=RED, title=f"⛔ Error: {error}")
    em.timestamp = dt.datetime.utcnow()
    return await ctx.send(embed=em)


def traceback(e: Exception):  # Converts an exception into the full traceback report
    return ''.join(tb.format_exception(None, e, e.__traceback__))


class Log(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: commands.Bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.guild.id != GUILD_ID:
            return
        if message.author.bot:  # ignore bots
            return
        if message.channel.id == LOG_ID:
            return

        desc = f"🗑️ **Message from {message.author.mention} deleted in {message.channel.mention}**\n" \
               f"{_crop(message.content)}"
        embed = discord.Embed(description=desc, colour=DELETE)
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.set_footer(text=f"User ID: {message.author.id}")
        embed.timestamp = dt.datetime.utcnow()

        channel = self.bot.get_channel(LOG_ID)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, old_message: discord.Message, message: discord.Message):
        if message.guild.id != GUILD_ID:
            return
        if message.author.bot:  # ignore bots
            return
        if old_message.content == message.content:
            return
        if message.channel.id == LOG_ID:
            return

        embed = discord.Embed(colour=EDIT, url=message.jump_url,
                              description=f"✏ **Message from {message.author.mention} edited in "
                                          f"{message.channel.mention}**")
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)

        embed.add_field(name="Old", value=_crop(old_message.content, chars=1024), inline=False)
        embed.add_field(name="New", value=_crop(message.content, chars=1024), inline=False)
        embed.set_footer(text=f"User ID: {message.author.id}")
        embed.timestamp = dt.datetime.utcnow()
        channel = self.bot.get_channel(LOG_ID)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, old: discord.Member, new: discord.Member):
        if new.guild.id != GUILD_ID:
            return

        channel = self.bot.get_channel(LOG_ID)

        if old.display_name != new.display_name:  # if nickname changed
            embed = discord.Embed(colour=NICKNAME, description=f"✏ **{new.mention}'s nickname was changed**")
            embed.set_author(name=new.display_name, icon_url=new.display_avatar.url)
            embed.add_field(name="Old", value=old.display_name, inline=False)
            embed.add_field(name="New", value=new.display_name, inline=False)
            embed.timestamp = dt.datetime.utcnow()

            await channel.send(embed=embed)

        elif old.roles != new.roles:  # if roles were changed
            if [x for x in old.roles if x not in new.roles]:  # role removed
                aor = "removed from"
                role = [x for x in old.roles if x not in new.roles][0]
            elif [x for x in new.roles if x not in old.roles]:  # role added
                aor = "assigned to"
                role = [x for x in new.roles if x not in old.roles][0]
            else:
                return

            # format embed
            embed = discord.Embed(colour=ROLE, description=f"🔰 **Role {aor} {new.mention}**")
            embed.add_field(name="Role:", value=role, inline=False)
            embed.set_author(name=new.display_name, icon_url=new.display_avatar.url)
            embed.timestamp = dt.datetime.utcnow()

            await channel.send(embed=embed)

        if old.timeout_until != new.timeout_until:  # Timeout has changed
            if new.timed_out:  # Is timed out
                embed = discord.Embed(colour=ROLE, description=f"🔇 **Timed out**")
                embed.add_field(name="Duration",
                                value=format_time(new.timeout_until - dt.datetime.now(dt.timezone.utc), "second"))
                embed.add_field(name="Unmute", value=discord.utils.format_dt(new.timeout_until, "R"))
                embed.set_author(name=new.display_name, icon_url=new.display_avatar.url)
                embed.timestamp = dt.datetime.utcnow()

                await channel.send(embed=embed)
            else:
                embed = discord.Embed(colour=ROLE, description=f"🔇 **Timeout removed**")
                embed.set_author(name=new.display_name, icon_url=new.display_avatar.url)
                embed.timestamp = dt.datetime.utcnow()

                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return

        embed = discord.Embed(colour=JOIN, description=member.mention, title="📥 User Joined")
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")
        embed.timestamp = dt.datetime.utcnow()

        channel = self.bot.get_channel(LOG_ID)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return

        embed = discord.Embed(colour=LEAVE, description=member.mention, title="📤 User Left")
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")
        embed.timestamp = dt.datetime.utcnow()

        channel = self.bot.get_channel(LOG_ID)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """
        Handle all errors from commands by default
        """
        error = getattr(error, "original", error)  # strip traceback
        if hasattr(ctx.command, "on_error"):
            # if command handles its own errors
            return
        if isinstance(error, commands.CommandNotFound):
            # if someone makes up a command or accidentally types the prefix, ignore it
            return
        elif isinstance(error, commands.MissingRole) or isinstance(error, commands.NotOwner):
            # ignore if user doesn't have perms for command
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await error_embed(ctx, f"Your command is missing the `{error.param.name}` argument")
        elif isinstance(error, commands.BadArgument) or isinstance(error, commands.BadUnionArgument):
            await error_embed(ctx, "A bad argument was passed")
        elif isinstance(error, commands.ArgumentParsingError):
            await error_embed(ctx, "Your arguments were formatted incorrectly")
        elif isinstance(error, commands.CommandOnCooldown):
            time = ceil(error.retry_after)
            em = discord.Embed(colour=RED, title="⛔ Error: Command on cooldown",
                               description=f"Try again in {time} seconds")
            em.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
            em.timestamp = dt.datetime.utcnow()
            await ctx.reply(embed=em, delete_after=time)
        elif isinstance(error, discord.Forbidden):
            # Try and send an alert to the channel, or to the user
            try:
                await error_embed(ctx, "A permissions error occurred")
            except discord.Forbidden:
                try:
                    em = discord.Embed(colour=RED,
                                       title="⛔ Error: I do not have permission to send messages in that channel")
                    em.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
                    em.timestamp = dt.datetime.utcnow()
                    await ctx.author.send(embed=em)
                except discord.DiscordException:
                    pass
        else:  # Unknown/unhandled exception
            em = discord.Embed(colour=RED, title=f"⛔ Unknown Error Occurred")
            em.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
            em.timestamp = dt.datetime.utcnow()
            await ctx.send(embed=em)

            # TODO - Ideally we would send as many lines of the traceback as we can fit
            error_text = traceback(error)
            # Will send the traceback if we have enough space, otherwise just send what the error was
            content = f"Error in {ctx.message.jump_url}\n```{error_text if len(error_text) < 1500 else error}```"
            channel = self.bot.get_channel(LOG_ID)
            await channel.send(content)


def setup(bot):
    bot.add_cog(Log(bot))
