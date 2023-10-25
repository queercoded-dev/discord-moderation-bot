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

        # Respond with selection
        await interaction.response.send_message("Updated roles!", ephemeral=True)


class RoleMenu(discord.ui.View):
    def __init__(self, config: dict):
        super().__init__(timeout=None)

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

        with open("roles.yaml") as fd:
            self.role_config = yaml.full_load(fd)

    @discord.message_command(name="Attach role menu")
    @discord.default_permissions(manage_messages=True)
    async def attach_roles(self, ctx: discord.ApplicationContext, message: discord.Message):
        """
        Attach the role menu to a message
        """
        if message.author.id != self.bot.user.id:
            await ctx.respond("The selected message must have been sent by the bot", ephemeral=True)
        else:
            await message.edit(view=RoleMenu(self.role_config))
            await ctx.respond("Attached", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(RoleMenu(self.role_config))

    @commands.Cog.listener()
    async def on_member_update(self, old_member: discord.Member, new_member: discord.Member):
        """
        When a role is added or removed, look up what category it is in and determine whether to add a header role
        """
        if len(old_member.roles) > len(new_member.roles):
            # Role must have been removed, so find an old role that isn't a new role
            role = [role for role in old_member.roles if role not in new_member.roles][0]
        elif len(old_member.roles) < len(new_member.roles):
            # Role has been added so find a new role that isn't an old role
            role = [role for role in new_member.roles if role not in old_member.roles][0]
        else:
            # Some other kind of update
            return

        await self.process_roles(new_member, role)

    async def process_roles(self, member: discord.Member, changed_role: discord.Role):
        for detail in self.role_config.values():
            divider_id = detail.get("divider")
            if not divider_id:
                continue

            roles = [x["id"] for x in detail.get("roles", {}).values()]

            if changed_role.id in roles:
                # We have found the category this role belongs to

                # Determine if we need to add or remove the divider

                has_roles_in_category = False

                for role_id in roles:
                    role = member.guild.get_role(role_id)
                    if role in member.roles:
                        has_roles_in_category = True
                        break

                # Apply the changes

                divider = member.guild.get_role(divider_id)
                if has_roles_in_category and divider not in member.roles:
                    await member.add_roles(divider, reason="Divider role.")
                elif not has_roles_in_category and divider in member.roles:
                    await member.remove_roles(divider, reason="Divider role.")

                # Don't process other categories since we have already matched one
                return


def setup(bot):
    bot.add_cog(Roles(bot))
