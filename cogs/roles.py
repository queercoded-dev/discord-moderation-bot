from discord.ext import commands
import discord
from config import GUILD_ID, MOD_ID

PRONOUNS_DIVIDER = 931027735474753556
PRONOUNS_VIEW = {
    "he/him": {"roleId": 931028572083216444},
    "she/her": {"roleId": 931028641654132816},
    "they/them": {"roleId": 931028678396227594},
    "Any": {"roleId": 931029765794717776},
    "Other/Ask me": {"roleId": 931028748973768825},
}

COLOURS_VIEW = {
    "Silver": {"roleId": 938915036330606692},
    "Gray": {"roleId": 938914712115101817},
    "Red": {"roleId": 938909726945722438},
    "Maroon": {"roleId": 938915198272671786},
    "Yellow": {"roleId": 938912658936180757},
    "Olive": {"roleId": 938913871282978846},
    "Lime": {"roleId": 938912477570301952},
    "Green": {"roleId": 938913738210291752},
    "Aqua": {"roleId": 938912702066216971},
    "Teal": {"roleId": 938913907165253672},
    "Blue": {"roleId": 938912524521336874},
    "Navy": {"roleId": 938913720866844714},
    "Fuchsia": {"roleId": 938912572420268072},
    "Purple": {"roleId": 938913675195080774},
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
    "3D Printing": {"roleId": 928723382751592518, "emoji": "3dprinting:933127502711361607"},
    "Circuits": {"roleId": 928724312502988820, "emoji": "transistor:933129000941912144"},
    "Cyber Security": {"roleId": 928724530673901669, "emoji": "firewall:933127502921105408"},
    "Game Dev/Modding": {"roleId": 933008738103742464, "emoji": "gamedev:933127502451331093"},
    "Networking": {"roleId": 928785182406873188, "emoji": "router:933127503902543883"},
    "Programming": {"roleId": 928786544440000522, "emoji": "code:933127502963048488"},
    "Ping": {"roleId": 934851594204360756, "emoji": "ping:934853400254894110"},
}

OS_DIVIDER = 928737228539174992
OS_VIEW = {
    "Arch": {"roleId": 928737067851206696, "emoji": "arch:927947448788353104"},
    "BSD": {"roleId": 928780279802372136, "emoji": "bsd:927947447139958795"},
    "Debian/Ubuntu": {"roleId": 928736847755116574, "emoji": "debian:927947446875734096"},
    "Fedora/RedHat": {"roleId": 928736994643837038, "emoji": "fedora:927947448301785130"},
    "Linux": {"roleId": 928722740821753937, "emoji": "linux:927948388853506138"},
    "MacOS": {"roleId": 928722779161890816, "emoji": "apple:931974640455274506"},
    "Windows": {"roleId": 928722827765481502, "emoji": "windows:927947446565371904"},
}


class View(discord.ui.View):
    def __init__(self, items=None, **kwargs):
        super().__init__(**kwargs)
        if items:
            self.add_item(items)


class RoleDropdown(discord.ui.Select):
    def __init__(self, view, divider: int, max, member: discord.Member):
        self.role_view = view
        self.divider = divider
        self.member = member
        self.max = max

        roles = [x.id for x in member.roles]
        options = [
            discord.SelectOption(label=name, default=value["roleId"] in roles,
                                 emoji=value["emoji"] if "emoji" in value else None)
            for name, value in view.items()
        ]

        super().__init__(placeholder="Select your roles", options=options,
                         min_values=0, max_values=len(view))

    async def callback(self, interaction: discord.Interaction):
        member = self.member.guild.get_member(self.member.id)  # Ensure the member object is up to date

        # Add or remove roles as needed
        for name, value in self.role_view.items():
            role_id = value["roleId"]
            role = self.member.guild.get_role(role_id)

            if name in self.values and role not in member.roles:  # role is selected and not assigned yet
                await self.member.add_roles(role, reason="Reaction role.")
            elif name not in self.values and role in member.roles:  # Not selected and is assigned
                await self.member.remove_roles(role, reason="Reaction role.")

        # Assign divider if given and needed
        if divider is not None:
            divider_role = self.member.guild.get_role(self.divider)
            if self.values and divider_role not in member.roles:
                await self.member.add_roles(divider_role, reason="Divider role.")
            elif not self.values and divider_role in member.roles:
                await self.member.remove_roles(divider_role, reason="Divider role.")

        # Respond with selection
        await interaction.response.send_message("Updated roles!", ephemeral=True)


class RoleMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="🏷", label="Pronouns", custom_id="RoleMenu_Pronouns")
    async def pronouns(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = View(RoleDropdown(PRONOUNS_VIEW, PRONOUNS_DIVIDER, len(PRONOUNS_VIEW), interaction.user))
        await interaction.response.send_message("Please select your pronouns roles below.",
                                                view=view, ephemeral=True)

    @discord.ui.button(emoji="🎨", label="Colours", custom_id="RoleMenu_Colours")
    async def pronouns(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = View(RoleDropdown(COLOURS_VIEW, None, 1, interaction.user))
        await interaction.response.send_message("Please select a colour from the roles below",
                                                view=view, ephemeral=True)

    @discord.ui.button(emoji="⌨️", label="Languages", custom_id="RoleMenu_Languages")
    async def languages(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = View(RoleDropdown(LANGUAGE_VIEW, LANG_DIVIDER, len(LANGUAGE_VIEW), interaction.user))
        await interaction.response.send_message("Please select from the language roles below.",
                                                view=view, ephemeral=True)

    @discord.ui.button(emoji="🖥️", label="OS", custom_id="RoleMenu_OS")
    async def os(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = View(RoleDropdown(OS_VIEW, OS_DIVIDER, len(OS_VIEW), interaction.user))
        await interaction.response.send_message("Please select from the OS roles below.",
                                                view=view, ephemeral=True)

    @discord.ui.button(emoji="🗂️", label="Interests", custom_id="RoleMenu_Interests")
    async def interests(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = View(RoleDropdown(INTEREST_VIEW, INTEREST_DIVIDER, len(INTEREST_DIVIDER), interaction.user))
        await interaction.response.send_message("Please select from the interest roles below.",
                                                view=view, ephemeral=True)


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: commands.Bot

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[GUILD_ID])
    async def pronounroles(self, ctx: commands.Context):
        """Creates a role picker for your pronouns"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        view = View(RoleDropdown(PRONOUNS_VIEW, PRONOUNS_DIVIDER, ctx.author))
        await ctx.send("Please select your pronouns roles below.", view=view, ephemeral=True)

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[GUILD_ID])
    async def colourroles(self, ctx: commands.Context):
        """Creates a role picker for colours"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        view = View(RoleDropdown(COLOURS_VIEW, None, ctx.author))
        await ctx.send("Please select a colour from the roles below.", view=view, ephemeral=True)

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[GUILD_ID])
    async def langroles(self, ctx: commands.Context):
        """Creates a role picker for programming languages"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        view = View(RoleDropdown(LANGUAGE_VIEW, LANG_DIVIDER, ctx.author))
        await ctx.send("Please select from the language roles below.", view=view, ephemeral=True)

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[GUILD_ID])
    async def interestroles(self, ctx: commands.Context):
        """Creates a role picker for interests"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        view = View(RoleDropdown(INTEREST_VIEW, INTEREST_DIVIDER, ctx.author))
        await ctx.send("Please select from the interest roles below.", view=view, ephemeral=True)

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[GUILD_ID])
    async def osroles(self, ctx: commands.Context):
        """Creates a role picker for operating systems"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        view = View(RoleDropdown(OS_VIEW, OS_DIVIDER, ctx.author))
        await ctx.send("Please select from the OS roles below.", view=view, ephemeral=True)

    @commands.command()
    @commands.has_role(MOD_ID)
    async def attachroles(self, ctx, message: discord.Message):
        if message.author.id != self.bot.user.id:
            raise commands.BadArgument

        await message.edit(view=RoleMenu())

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(RoleMenu())


def setup(bot):
    bot.add_cog(Roles(bot))
