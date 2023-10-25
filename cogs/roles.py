from discord.ext import commands
import discord
import yaml


class View(discord.ui.View):
    def __init__(self, items: discord.ui.Item = None, **kwargs):
        super().__init__(**kwargs)
        if items:
            self.add_item(items)


class RoleDropdown(discord.ui.Select):
    def __init__(self, view, member: discord.Member, divider: int = None, max_roles: int = None):
        self.role_view = view
        self.divider = divider
        self.member = member
        self.max = max_roles if max_roles is not None else len(view)

        roles = [x.id for x in member.roles]
        options = [
            discord.SelectOption(label=name, default=value["id"] in roles,
                                 emoji=value["emoji"] if "emoji" in value else None)
            for name, value in view.items()
        ]

        super().__init__(placeholder="Select your roles", options=options,
                         min_values=0, max_values=self.max)

    async def callback(self, interaction: discord.Interaction):
        member = self.member.guild.get_member(self.member.id)  # Ensure the member object is up to date

        # Add or remove roles as needed
        for name, value in self.role_view.items():
            role_id = value["id"]
            role = self.member.guild.get_role(role_id)

            if name in self.values and role not in member.roles:  # role is selected and not assigned yet
                await self.member.add_roles(role, reason="Reaction role.")
            elif name not in self.values and role in member.roles:  # Not selected and is assigned
                await self.member.remove_roles(role, reason="Reaction role.")

        # Assign divider if given and needed
        if self.divider is not None:
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

        with open("roles.yaml") as fd:
            config = yaml.full_load(fd)

        for name, values in config.items():
            def make_callback(name_, values_):
                # Command body
                async def callback(interaction: discord.Interaction, _=None):  # _=None to satisfy self param
                    # Respond with corresponding dropdown
                    view = View(RoleDropdown(values_["roles"], interaction.user, divider=values_.get("divider")))
                    await interaction.response.send_message(f"Please select your {name_.lower()} roles below:",
                                                            view=view, ephemeral=True)

                return callback

            # Add button
            button = discord.ui.Button(emoji=values.get("emoji"), label=name, custom_id="RoleMenu_" + name,
                                       row=values["row"])
            button.callback = make_callback(name, values)
            self.add_item(button)


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: commands.Bot

    @discord.message_command(name="Attach role menu")
    @discord.default_permissions(manage_messages=True)
    async def attach_roles(self, ctx: discord.ApplicationContext, message: discord.Message):
        """
        Attach the role menu to a message
        """
        if message.author.id != self.bot.user.id:
            await ctx.respond("The selected message must have been sent by the bot", ephemeral=True)
        else:
            await message.edit(view=RoleMenu())
            await ctx.respond("Attached", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(RoleMenu())


def setup(bot):
    bot.add_cog(Roles(bot))
