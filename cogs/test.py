from discord.ext import commands
import discord
from discord.ui import View, Select


class Test(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.select(custom_id="Testing", placeholder="Testing", min_values=1, max_values=1, options=[
        discord.SelectOption(label="First option", value="Linux", emoji="linux:927948388853506138"),
        discord.SelectOption(label="Second option", value="Ruby", emoji="ruby:927947448528273408"),
        discord.SelectOption(label="Third option", value="Arch", emoji="arch:927947448788353104")])
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.send_message(f"You Selected {select.values}  !", ephemeral=False)


class TestingCog(commands.Cog, name="TestingCog"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx):
        view = Test(ctx)
        await ctx.send("Testing the select menu!", view=view)


def setup(bot):
    bot.add_cog(TestingCog(bot))
