from discord.ext import commands
import discord
from config import LOG_ID

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

INTEREST_VIEW = {
    "Programming": {"roleId": 928786544440000522, "emoji": "code:928786531081150495"},
    "3D Printing": {"roleId": 928723382751592518, "emoji": "3dprinting:928790227248635945"},
    "Cyber Security": {"roleId": 928724530673901669, "emoji": "firewall:928790564953010266"},
    "Networking": {"roleId": 928785182406873188, "emoji": "router:928791011675762798"},
    "Circuits": {"roleId": 928724312502988820, "emoji": "transistor:927947446791831602"}
}

OS_VIEW = {
    "Linux": {"roleId": 928722740821753937, "emoji": "linux:927948388853506138"},
    "MacOS": {"roleId": 928722779161890816, "emoji": "apple:927947449170026496"},
    "Windows": {"roleId": 928722827765481502, "emoji": "windows:927947446565371904"},
    "Debian/Ubuntu": {"roleId": 928736847755116574, "emoji": "debian:927947446875734096"},
    "Arch": {"roleId": 928737067851206696, "emoji": "arch:927947448788353104"},
    "BSD": {"roleId": 928780279802372136, "emoji": "bsd:927947447139958795"}
}


class LangReactView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__()
        self.ctx = ctx

    @discord.ui.select(custom_id="Language Reaction Menu", placeholder="Please Select Your Languages.",
                       min_values=1, max_values=12,
                       options=[discord.SelectOption(label=name, emoji=value["emoji"])
                                for name, value in LANGUAGE_VIEW.items()])
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        for language in select.values:
            role_id = LANGUAGE_VIEW[language]["roleId"]
            language_divider = self.ctx.guild.get_role(928722640867319859) # Language divider
            role = self.ctx.guild.get_role(role_id)
            await self.ctx.author.add_roles(role, reason=f"Reaction role.")
            try:
                await self.ctx.author.add_roles(language_divider, reason=f"Language divider added.")
            except discord.HTTPException:
                LogChannel = self.ctx.guild.get_channel(LOG_ID)
                await LogChannel.send(f"Failed to add divider role!")

        languages = ", ".join(select.values)
        await interaction.response.send_message(f"You chose: {languages}!", ephemeral=True)
        await interaction.channel.purge(limit=1)  # Deletes interaction message once done

class InterestsReactView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__()
        self.ctx = ctx

    @discord.ui.select(custom_id="Interest Reaction Menu", placeholder="Please Select Your Interest.",
                       min_values=1, max_values=5,
                       options=[discord.SelectOption(label=name, emoji=value["emoji"])
                                for name, value in INTEREST_VIEW.items()])
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        for interest in select.values:
            role_id = INTEREST_VIEW[interest]["roleId"]
            role = self.ctx.guild.get_role(role_id)
            interest_divider = self.ctx.guild.get_role(928722640867319859)  # Interest Divider
            await self.ctx.author.add_roles(role, reason=f"Reaction role.")
            try:
                await self.ctx.author.add_roles(interest_divider, reason=f"Interest Divider added.")
            except discord.HTTPException:
                LogChannel = self.ctx.guild.get_channel(LOG_ID)
                await LogChannel.send(f"Failed to add divider role!")

        interests = ", ".join(select.values)
        await interaction.response.send_message(f"You chose: {interests}!", ephemeral=True)
        await interaction.channel.purge(limit=1)  # Deletes interaction message once done


class OSReactView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__()
        self.ctx = ctx

    @discord.ui.select(custom_id="Operating System Reaction Menu", placeholder="Please Select Your Operating Systems.",
                       min_values=1, max_values=6,
                       options=[discord.SelectOption(label=name, emoji=value["emoji"])
                                for name, value in OS_VIEW.items()])
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        for os in select.values:
            role_id = OS_VIEW[os]["roleId"]
            role = self.ctx.guild.get_role(role_id)
            os_divider = self.ctx.guild.get_role(928737228539174992)
            await self.ctx.author.add_roles(role, reason=f"Reaction role.")
            try:
                await self.ctx.author.add_roles(os_divider, reason=f"OS Divider added")
            except discord.HTTPException:
                LogChannel = self.ctx.guild.get_channel(LOG_ID)
                await LogChannel.send(f"Failed to add divider role!")

        osystems = ", ".join(select.values)
        await interaction.response.send_message(f"You chose: {osystems}!", ephemeral=True)
        await interaction.channel.purge(limit=1)  # Deletes interaction message once done


class ReactionCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: commands.Bot

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[925804557001437184])
    async def langrole(self, ctx: commands.Context):
        """Creates a role picker for languages"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        await ctx.send("Please select from the language roles below.", view=LangReactView(ctx))

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[925804557001437184])
    async def interestrole(self, ctx: commands.Context):
        """Creates a role picker for languages"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        await ctx.send("Please select from the interest roles below.", view=InterestsReactView(ctx))

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[925804557001437184])
    async def osrole(self, ctx: commands.Context):
        """Creates a role picker for languages"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        await ctx.send("Please select from the OS roles below.", view=OSReactView(ctx))


def setup(bot):
    bot.add_cog(ReactionCreate(bot))
