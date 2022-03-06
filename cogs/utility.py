import discord
from discord.ext import commands
from config import GUILD_ID, MAIN
from utils.utils import LETTERS


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def poll(self, ctx: commands.Context, question, *, options):
        """
        Create a poll
        Each poll option should be placed on a new line
        """
        em = discord.Embed(title=f"📊 {question}", colour=MAIN, timestamp=discord.utils.utcnow(), description="")
        em.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

        options = options.split("\n")

        lines = 0  # Number of lines we were able to add to the embed
        for index, option in enumerate(options[:len(LETTERS)]):
            line = f"\n{LETTERS[index]} {option}"
            if len(em.description + line) < 4096:
                em.description += line
                lines = index
            else:
                break

        msg = await ctx.send(embed=em)

        for i in range(lines + 1):
            await msg.add_reaction(LETTERS[i])


def setup(bot):
    bot.add_cog(Utility(bot))
