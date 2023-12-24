import discord
from discord.ext import commands
from config import MAIN
from utils.utils import LETTERS
import datetime as dt


class PollModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="New Poll")

        self.add_item(discord.ui.InputText(label="Question"))
        self.add_item(discord.ui.InputText(label="Options", placeholder="Enter each answer on a new line",
                                           style=discord.InputTextStyle.multiline))

    async def callback(self, interaction: discord.Interaction):
        question = self.children[0].value
        options = self.children[1].value.split("\n")

        em = discord.Embed(title=f"📊 {question}", colour=MAIN, description="")

        lines = 0  # Number of lines we were able to add to the embed
        for index, option in enumerate(options[:len(LETTERS)]):
            line = f"\n{LETTERS[index]} {option}"
            if len(em.description + line) < 4096:
                em.description += line
                lines = index
            else:
                break

        await interaction.response.send_message(embed=em)
        message = await interaction.original_message()

        for i in range(lines + 1):
            await message.add_reaction(LETTERS[i])


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command()
    async def poll(self, ctx: discord.ApplicationContext):
        """Create a poll"""
        await ctx.send_modal(PollModal())

    @discord.slash_command()
    @discord.option("units", description="The unit the duration is in", choices=[
        discord.OptionChoice(name="Minutes", value=60),
        discord.OptionChoice(name="Hours", value=60 * 60),
        discord.OptionChoice(name="Days", value=24 * 60 * 60)])
    async def eep(self, ctx: discord.ApplicationContext, time: discord.Option(int), units: int):
        """
        Temporarily mute yourself. Can only be reversed by a mod
        """
        delta = dt.timedelta(seconds=time * units)
        if delta.days > 28:
            await ctx.respond("The max timeout is 28 days", ephemeral=True)
        else:
            try:
                await ctx.user.timeout_for(delta, reason="Selfmute")
            except discord.Forbidden:
                await ctx.respond(f"I do not have permission to apply a timeout to you", ephemeral=True)
            else:
                timeout_end = discord.utils.format_dt(dt.datetime.now() + delta)
                await ctx.respond(f"Ok, I will mute you until {timeout_end}")

    @discord.slash_command()
    async def notabot(self, ctx: discord.ApplicationContext):
        """
        Displays a quick message to explain plurality
        """
        embed = discord.Embed(colour=MAIN)
        embed.set_footer(icon_url=ctx.author.avatar.url, text=f"Summoned by {ctx.author.display_name}")

        embed.description = "This server has a system that allows people to communicate though a proxy.\nThis " \
                            "benefits people who experience [plurality](https://morethanone.info/). In the serious " \
                            "category channels, they can be used for anonymity.\n\nDue to the way this system works, " \
                            "some messages may show up with a [BOT] however these messages are still sent by normal " \
                            "people and thus should be treated as such."

        await ctx.respond(embed=embed)



def setup(bot):
    bot.add_cog(Utility(bot))
