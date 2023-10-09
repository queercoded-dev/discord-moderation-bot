from discord.ext import commands
import discord
from time import perf_counter


class Meta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: commands.Bot

    @discord.slash_command()
    async def ping(self, ctx: discord.ApplicationContext):
        """
        Ping!
        """
        start = perf_counter()
        message = await ctx.respond(f"Measuring latency...")
        end = perf_counter()
        duration = (end - start) * 1000
        msg = f"Pong!\nDiscord latency: {self.bot.latency * 1000:.0f}ms\nBot Latency: {duration:.0f}ms"
        await message.edit_original_message(content=msg)


def setup(bot):
    bot.add_cog(Meta(bot))
