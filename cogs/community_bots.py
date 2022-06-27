import discord
from discord.ext import commands
from config import GUILD_ID, MAIN, BOT_VERIFICATION_ID, COMMUNITY_BOTS_ID, MOD_ID
from utils.utils import utc_now

PREAMBLE = f"""**Community Bot Applications:**
Please read through the following conditions before applying.

1. Bots will only be given access to <#{COMMUNITY_BOTS_ID}>
2. Bots will only be given basic non-administrative permissions within that channel (send message, add reactions etc.)
3. Bots must adhere by all server rules (no NSFW, spam etc.)
4. Bots must not send unsolicited pings or DMs to other users.

Bots that circumvent these rules will be kicked at the moderators' discretion.
Depending on the severity, punishments may extend to the user who added the bot."""


def bot_invite(bot_id: int):
    return discord.utils.oauth_url(bot_id, guild=discord.Object(GUILD_ID), disable_guild_select=True,
                                   scopes=("bot", "applications.commands"))


class Accept(discord.ui.View):
    # If modals had descriptions, we would use that, instead use an ephemeral "T&Cs" thing
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, _button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(Modal(self.bot))
        # Sadly can't delete ephemeral messages


class Modal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        super().__init__(title="Bot Application:", custom_id="CommunityBotApp")

        self.add_item(
            discord.ui.InputText(label="Bot ID", placeholder="Bot ID", min_length=15, max_length=20)
        )
        self.add_item(
            discord.ui.InputText(label="Tell Us About Your Bot",
                                 placeholder="What does your bot do?\n"
                                             "Provide a link to your bots homepage/repo if you have one",
                                 style=discord.InputTextStyle.paragraph)
        )

    async def callback(self, interaction: discord.Interaction):
        # Try and convert the bot id to an int
        try:
            bot_id = int(self.children[0].value)
        except ValueError:
            await interaction.response.send_message("Invalid bot ID", ephemeral=True)
            return

        reason = self.children[1].value  # type: str

        # Check if ID corresponds to a bot account
        bot = await self.bot.get_or_fetch_user(bot_id)
        if not bot or not bot.bot:
            await interaction.response.send_message("That user ID does not correspond to a bot account", ephemeral=True)
            return

        # Build embed
        em = discord.Embed(colour=MAIN, timestamp=utc_now())
        em.set_author(name=bot.name, icon_url=bot.display_avatar.url)
        em.add_field(name="Info", inline=False,
                     value=f"User: {interaction.user.mention} ({interaction.user.id}) \nBot: <@{bot_id}> {bot_id}")
        em.add_field(name="Reason", value=reason, inline=False)
        em.set_footer(text=f"Submitted by: {interaction.user.name}",
                      icon_url=interaction.user.display_avatar.url)

        # Send application
        view = BotApplication(self.bot, bot, interaction.user)
        channel = self.bot.get_channel(BOT_VERIFICATION_ID)
        await channel.send("New Bot Application:", embed=em, view=view)

        # Send response
        try:
            await interaction.user.send("Community bot application submitted\n"
                                        "Please be patient while our mod team reviews the application", embed=em)
        except discord.Forbidden:
            channel = self.bot.get_channel(COMMUNITY_BOTS_ID)
            await channel.send(f"{interaction.user.mention} application submitted\n"
                               f"Please be patient while our mod team reviews the application", embed=em)
        # Modals require an interaction response :/
        await interaction.response.send_message("Application received", ephemeral=True)


class BotApplication(discord.ui.View):
    def __init__(self, bot: commands.Bot, target_bot: discord.User, user: discord.User):
        self.bot = bot
        self.targetBot = target_bot
        self.user = user

        super().__init__()

        # Create invite button
        self.add_item(
            discord.ui.Button(label="Invite", url=bot_invite(self.targetBot.id))
        )

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success)
    async def approve(self, _button: discord.Button, interaction: discord.Interaction):
        guild = self.bot.get_guild(GUILD_ID).name
        # {{}} allows us to use .format later on
        message = f"Hey {{}}, your application to add `{self.targetBot.name}` to {guild} has been approved!\n" \
                  f"You will be able to use your bot within <#{COMMUNITY_BOTS_ID}>"

        # DM or @ user with message
        try:
            await self.user.send(message.format(self.user.name))
        except discord.Forbidden:
            channel = self.bot.get_channel(COMMUNITY_BOTS_ID)
            await channel.send(message.format(self.user.mention))

        self.stop()

        # In case the application was approved but the bot wasn't invited, keep the invite button
        backup_view = discord.ui.View()
        backup_view.add_item(
            discord.ui.Button(label="Invite", url=bot_invite(self.targetBot.id))
        )

        await interaction.message.edit(content="Application approved", view=backup_view)
        await interaction.response.defer()  # Mark interaction as completed

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny(self, _button: discord.Button, interaction: discord.Interaction):
        guild = self.bot.get_guild(GUILD_ID).name
        message = f"Hey {{}}, your application to add `{self.targetBot.name}` to {guild} has been denied\n" \
                  f"Make sure your bot is public and follows our community bot rules."

        # DM or @ user with message
        try:
            await self.user.send(message.format(self.user.name))
        except discord.Forbidden:
            channel = self.bot.get_channel(COMMUNITY_BOTS_ID)
            await channel.send(message.format(self.user.mention))

        self.stop()
        await interaction.message.edit(content="Application denied", view=None)
        await interaction.response.defer()  # Mark interaction as completed

    async def interaction_check(self, interaction: discord.Interaction):
        return discord.utils.get(interaction.user.roles, id=MOD_ID)


class CommunityBots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(guild_ids=[GUILD_ID])
    async def addbot(self, ctx: discord.ApplicationContext):
        """
        Apply to have your bot added to our server
        """
        await ctx.respond(PREAMBLE, view=Accept(self.bot), ephemeral=True)

    @commands.command()
    @commands.has_role(MOD_ID)
    async def botinvite(self, ctx: commands.Context, bot_id: int):
        """
        Manually create a community bot invite url
        """
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(label="Invite", url=bot_invite(bot_id))
        )
        await ctx.send("Use the button below to invite your bot", view=view)


def setup(bot):
    bot.add_cog(CommunityBots(bot))
