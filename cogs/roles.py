from discord.ext import commands
import discord
from config import GUILD_ID

PRONOUNS_DIVIDER = 931027735474753556
PRONOUNS_VIEW = {
    "he/him": {"roleId": 931028572083216444},
    "she/her": {"roleId": 931028641654132816},
    "they/them": {"roleId": 931028678396227594},
    "Any": {"roleId": 931029765794717776},
    "Other/Ask me": {"roleId": 931028748973768825},
}

LANG_DIVIDER = 928718017678958613
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

INTEREST_DIVIDER = 928722640867319859
INTEREST_VIEW = {
    "Programming": {"roleId": 928786544440000522, "emoji": "code:928786531081150495"},
    "3D Printing": {"roleId": 928723382751592518, "emoji": "3dprinting:928790227248635945"},
    "Cyber Security": {"roleId": 928724530673901669, "emoji": "firewall:928790564953010266"},
    "Networking": {"roleId": 928785182406873188, "emoji": "router:928791011675762798"},
    "Circuits": {"roleId": 928724312502988820, "emoji": "transistor:927947446791831602"}
}

OS_DIVIDER = 928737228539174992
OS_VIEW = {
    "Linux": {"roleId": 928722740821753937, "emoji": "linux:927948388853506138"},
    "MacOS": {"roleId": 928722779161890816, "emoji": "apple:927947449170026496"},
    "Windows": {"roleId": 928722827765481502, "emoji": "windows:927947446565371904"},
    "Debian/Ubuntu": {"roleId": 928736847755116574, "emoji": "debian:927947446875734096"},
    "Arch": {"roleId": 928737067851206696, "emoji": "arch:927947448788353104"},
    "BSD": {"roleId": 928780279802372136, "emoji": "bsd:927947447139958795"}
}


class View(discord.ui.View):
    def __init__(self, items):
        super().__init__()
        self.add_item(items)


class RoleDropdown(discord.ui.Select):
    def __init__(self, view, divider: int, ctx: commands.Context):
        self.role_view = view
        self.divider = divider
        self.ctx = ctx

        roles = [x.id for x in ctx.author.roles]
        options = [
            discord.SelectOption(label=name, default=value["roleId"] in roles,
                                 emoji=value["emoji"] if "emoji" in value else None)
            for name, value in view.items()
        ]

        super().__init__(placeholder="Select your roles", options=options,
                         min_values=0, max_values=len(view))

    async def callback(self, interaction: discord.Interaction):
        member = self.ctx.guild.get_member(self.ctx.author.id)  # Ensure the member object is up to date

        # Add or remove roles as needed
        for name, value in self.role_view.items():
            role_id = value["roleId"]
            role = self.ctx.guild.get_role(role_id)

            if name in self.values and role not in member.roles:  # role is selected and not assigned yet
                await self.ctx.author.add_roles(role, reason="Reaction role.")
            elif name not in self.values and role in member.roles:  # Not selected and is assigned
                await self.ctx.author.remove_roles(role, reason="Reaction role.")

        # Assign divider if needed
        divider_role = self.ctx.guild.get_role(self.divider)
        if self.values and divider_role not in member.roles:
            await self.ctx.author.add_roles(divider_role, reason="Divider role.")
        elif not self.values and divider_role in member.roles:
            await self.ctx.author.remove_roles(divider_role, reason="Divider role.")

        # Respond with selection
        await interaction.response.send_message("Updated roles!", ephemeral=True)


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: commands.Bot

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[GUILD_ID])
    async def pronounroles(self, ctx: commands.Context):
        """Creates a role picker for your pronouns"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        view = View(RoleDropdown(PRONOUNS_VIEW, PRONOUNS_DIVIDER, ctx))
        await ctx.send("Please select your pronouns roles below.", view=view, ephemeral=True)

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[GUILD_ID])
    async def langroles(self, ctx: commands.Context):
        """Creates a role picker for programming languages"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        view = View(RoleDropdown(LANGUAGE_VIEW, LANG_DIVIDER, ctx))
        await ctx.send("Please select from the language roles below.", view=view, ephemeral=True)

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[GUILD_ID])
    async def interestroles(self, ctx: commands.Context):
        """Creates a role picker for interests"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        view = View(RoleDropdown(INTEREST_VIEW, INTEREST_DIVIDER, ctx))
        await ctx.send("Please select from the interest roles below.", view=view, ephemeral=True)

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[GUILD_ID])
    async def osroles(self, ctx: commands.Context):
        """Creates a role picker for operating systems"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        view = View(RoleDropdown(OS_VIEW, OS_DIVIDER, ctx))
        await ctx.send("Please select from the OS roles below.", view=view, ephemeral=True)


def setup(bot):
    bot.add_cog(Roles(bot))
