from discord.ext import commands
import discord

LANGUAGE_VIEW = {
    "C": {"roleId": 927942745639780432, "emoji": "c_:927947447425204304"},
    "C#": {"roleId": 928784767254663228, "emoji": "csharp:928785241697583104"},
    "C++": {"roleId": 927950084329582652, "emoji": "cpp:927947734151999488"},
    "Go": {"roleId": 928780947925659698, "emoji": "go:927947447383253042"},
    "HTML/CSS": {"roleId": 928770500187009175, "emoji": "html:928791843741769739"},
    "Java": {"roleId": 927942713226190908, "emoji": "java:927947447311958057"},
    "Javascript": {"roleId": 927943172624105472, "emoji": "javascript:927947447022534696"},
    "Kotlin": {"roleId": 927950071721500792, "emoji": "kotlin:927948108351045642"},
    "PHP": {"roleId": 927943198381334598, "emoji": "php:927947447324536832"},
    "Python": {"roleId": 927942689381552138, "emoji": "python:927948531229139014"},
    "Ruby": {"roleId": 928780488896839820, "emoji": "ruby:927947448528273408"},
    "Rust": {"roleId": 927943241255505931, "emoji": "rust:928792599748288542"},
    "Typescript": {"roleId": 928780873267040266, "emoji": "typescript:927947446301106257"},
}


class ReactView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__()
        self.ctx = ctx

    @discord.ui.select(custom_id="Language Reaction Menu", placeholder="Please Select Your Languages.",
                       min_values=1, max_values=12,
                       options=[discord.SelectOption(label=name, emoji=value["emoji"]) for name, value in LANGUAGE_VIEW.items()]
                       )
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        for language in select.values:
            role_id = LANGUAGE_VIEW[language]["roleId"]
            role = self.ctx.guild.get_role(role_id)
            await self.ctx.author.add_roles(role, reason=f"Reaction role.")

        languages = ", ".join(select.values)
        await interaction.response.send_message(f"You chose: {languages}!", ephemeral=True)


class ReactionCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: commands.Bot

    @commands.command(slash_command=True, ephemeral=True)
    async def langreact(self, ctx: commands.Context):
        """Creates a role picker for languages"""
        await ctx.send("Select your language roles below.", view=ReactView(ctx))


def setup(bot):
    bot.add_cog(ReactionCreate(bot))
