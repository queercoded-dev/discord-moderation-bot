import discord
from discord.ext import commands
from config import MAIN
from utils.utils import LETTERS


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


def setup(bot):
    bot.add_cog(Utility(bot))
