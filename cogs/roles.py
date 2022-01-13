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


async def role_callback(view_data, divider: int,
                        ctx: commands.Context, select: discord.ui.Select, interaction: discord.Interaction):
    added_roles = []
    removed_roles = []
    author_roles = [x.id for x in ctx.author.roles]

    # Assign or remove roles as needed
    for selection in select.values:
        role_id = view_data[selection]["roleId"]
        role = ctx.guild.get_role(role_id)
        if role_id in author_roles:
            await ctx.author.remove_roles(role, reason="Reaction role.")
            author_roles.remove(role_id)  # list needs to be updated to reflect changes
            removed_roles.append(selection)
        else:
            await ctx.author.add_roles(role, reason="Reaction role.")
            author_roles.append(role_id)
            added_roles.append(selection)

    # Check if divider role needs to be assigned
    has_role_in_category = False
    for value in view_data.values():
        if value["roleId"] in author_roles:
            has_role_in_category = True
            break

    # Assign divider if needed
    divider_role = ctx.guild.get_role(divider)
    if has_role_in_category and divider not in author_roles:
        await ctx.author.add_roles(divider_role, reason="Divider role.")
    elif not has_role_in_category and divider in author_roles:
        await ctx.author.remove_roles(divider_role, reason="Divider role.")

    # Respond with selection
    added_roles = ", ".join(added_roles) if added_roles else "None"
    removed_roles = ", ".join(removed_roles) if removed_roles else "None"
    await interaction.response.send_message(f"Added: {added_roles}\nRemoved: {removed_roles}", ephemeral=True)
    await interaction.channel.purge(limit=1)  # Deletes interaction message once done


class PronounsReactView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__()
        self.ctx = ctx

    @discord.ui.select(custom_id="Pronoun Reaction Menu", placeholder="Please Select Your Pronouns.",
                       min_values=1, max_values=len(PRONOUNS_VIEW),
                       options=[discord.SelectOption(label=name) for name in PRONOUNS_VIEW.keys()])
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        await role_callback(PRONOUNS_VIEW, PRONOUNS_DIVIDER, self.ctx, select, interaction)


class LangReactView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__()
        self.ctx = ctx

    @discord.ui.select(custom_id="Language Reaction Menu", placeholder="Please Select Your Languages.",
                       min_values=1, max_values=len(LANGUAGE_VIEW),
                       options=[discord.SelectOption(label=name, emoji=value["emoji"])
                                for name, value in LANGUAGE_VIEW.items()])
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        await role_callback(LANGUAGE_VIEW, LANG_DIVIDER, self.ctx, select, interaction)


class InterestsReactView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__()
        self.ctx = ctx

    @discord.ui.select(custom_id="Interest Reaction Menu", placeholder="Please Select Your Interest.",
                       min_values=1, max_values=len(INTEREST_VIEW),
                       options=[discord.SelectOption(label=name, emoji=value["emoji"])
                                for name, value in INTEREST_VIEW.items()])
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        await role_callback(INTEREST_VIEW, INTEREST_DIVIDER, self.ctx, select, interaction)


class OSReactView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__()
        self.ctx = ctx

    @discord.ui.select(custom_id="Operating System Reaction Menu", placeholder="Please Select Your Operating Systems.",
                       min_values=1, max_values=len(OS_VIEW),
                       options=[discord.SelectOption(label=name, emoji=value["emoji"])
                                for name, value in OS_VIEW.items()])
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        await role_callback(OS_VIEW, OS_DIVIDER, self.ctx, select, interaction)


class ReactionCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: commands.Bot

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[GUILD_ID])
    async def pronounroles(self, ctx: commands.Context):
        """Creates a role picker for your pronouns"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        await ctx.send("Please select your pronouns roles below.", view=PronounsReactView(ctx))

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[GUILD_ID])
    async def langroles(self, ctx: commands.Context):
        """Creates a role picker for programming languages"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        await ctx.send("Please select from the language roles below.", view=LangReactView(ctx))

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[GUILD_ID])
    async def interestroles(self, ctx: commands.Context):
        """Creates a role picker for interests"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        await ctx.send("Please select from the interest roles below.", view=InterestsReactView(ctx))

    @commands.command(message_command=False, slash_command=True, ephemeral=True,
                      slash_command_guilds=[GUILD_ID])
    async def osroles(self, ctx: commands.Context):
        """Creates a role picker for operating systems"""
        await ctx.message.delete(delay=2)  # Deletes command in chat
        await ctx.send("Please select from the OS roles below.", view=OSReactView(ctx))


def setup(bot):
    bot.add_cog(ReactionCreate(bot))
