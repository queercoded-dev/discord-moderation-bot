from discord.ext import commands
import discord
from discord.ui import View, Select


class ReactView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.select(custom_id="Language Reaction Menu", placeholder="Please Select Your Languages.",
                       min_values=1, max_values=3, options=[
                            discord.SelectOption(label="Python",
                                                 value="Python", emoji="python:927948531229139014"),
                            discord.SelectOption(label="Rust",
                                                 value="Rust", emoji="rust:928792599748288542"),
                            discord.SelectOption(label="Java",
                                                 value="Java", emoji="java:927947447311958057"),
                            discord.SelectOption(label="Kotlin",
                                                 value="Kotlin", emoji="kotlin:927948108351045642"),
                            discord.SelectOption(label="Javascript",
                                                 value="Javascript", emoji="javascript:927947447022534696"),
                            discord.SelectOption(label="Typescript",
                                                 value="Typescript", emoji="typescript:927947446301106257"),
                            discord.SelectOption(label="C",
                                                 value="C", emoji="c_:927947447425204304"),
                            discord.SelectOption(label="C++",
                                                 value="c++", emoji="cpp:927947734151999488"),
                            discord.SelectOption(label="HTML/CSS",
                                                 value="HTML/CSS", emoji="html:928791843741769739"),
                            discord.SelectOption(label="PHP",
                                                 value="PHP", emoji="php:927947447324536832"),
                            discord.SelectOption(label="Ruby",
                                                 value="Ruby", emoji="ruby:927947448528273408"),
                            discord.SelectOption(label="Go",
                                                 value="Go", emoji="go:927947447383253042"),
                            discord.SelectOption(label="C#",
                                                 value="C#", emoji="csharp:928785241697583104")])
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        languages_dict = {
            "Python": 927942689381552138,
            "Rust": 927943241255505931,
            "Java": 927942713226190908,
            "Kotlin": 927950071721500792,
            "Javascript": 927943172624105472,
            "Typescript": 928780873267040266,
            "C": 927942745639780432,
            "C++": 927950084329582652,
            "HTML/CSS":  928770500187009175,
            "PHP": 927943198381334598,
            "Go": 928780947925659698,
            "C#": 928784767254663228
        }
        length = len(select.values)
        languages = ", ".join(select.values)
        user = await self.bot.guild.try_member(interaction.user.id)
        for language in select.values:
            role_id = languages_dict[language]
            role = self.bot.guild.get_role(role_id)
            await user.add_roles(role, reason=f"Reaction role.")

        await interaction.response.send_message(f"You chose: {languages}!",
                                                ephemeral=True)


class ReactionCreate(commands.Cog, name="ReactionCreate"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def LangReact(self, ctx):
        view = ReactView(ctx)
        await ctx.send("Testing the select menu!", view=view)


def setup(bot):
    bot.add_cog(ReactionCreate(bot))
