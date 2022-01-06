from discord.ext import commands
import discord
from discord.ui import View, Select


class ReactView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.select(custom_id="Testing", placeholder="Testing", min_values=1, max_values=3, options=[
        discord.SelectOption(label="First option", value="Python", emoji="python:927948531229139014"),
        discord.SelectOption(label="Second option", value="Ruby", emoji="ruby:927947448528273408"),
        discord.SelectOption(label="Third option", value="Arch", emoji="arch:927947448788353104")])
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if select.values[0] == "Python":
            role = self.bot.guild.get_role(927942689381552138)
            user = await self.bot.guild.fetch_member(interaction.user.id)
            await user.add_roles(role, reason="Reaction Role.")
            await interaction.response.send_message(f"You Selected python and I've added you to the role!",
                                                    ephemeral=False)
        else:
            await interaction.response.send_message(f"L", ephemeral=False)


class ReactionCreate(commands.Cog, name="TestingCog"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx):
        view = ReactView(ctx)
        await ctx.send("Testing the select menu!", view=view)


def setup(bot):
    bot.add_cog(ReactionCreate(bot))
