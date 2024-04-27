import discord
from discord.ext import commands
from config import VERIFY_WORDS, UNVERIFIED_ID, GUILD_ID, VERIFY_ID
from random import choice
from utils.db_utils import set_prop, get_prop
import asyncio
import datetime as dt

# The mongo collection to use for everything here
DB_COLL = "verification"
VERIFY_DURATION = dt.timedelta(minutes=10)

"""
Verification process is like this:

1. A user joins the server
2. Lookup if the user has been verified before:
     Yes: Do nothing
     No:  Continue
3. Add unverified role to user
     Hands off to role added listener

Verification button:
1. User verifies
2. Remove unverified role
    Hands off to role removed listener


Role added listener:
1. Enter in DB as unverified
2. Start a timer (in a subprocess)
3. At the end of the timer, check if the user is still marked as unverified
    Yes: Kick
    No:  Do nothing


Role removed listener:
1. Mark as verified in db

Notes:
- This could be done without roles but it allows for an easy interface
  for mods to mark users as verified and see who is/isnt verified
- Database use is necessary in order to remember if a user has previously joined
- Roles are considered the source of truth, db is only for the above
"""

async def is_verified(member: discord.Member) -> bool:
    return await get_prop(member.id, DB_COLL, "verified", False) == True


class VerifyButton(discord.ui.View):
    def __init__(self, role):
        super().__init__(timeout=None)
        self.unverified_role = role
                                    
    @discord.ui.button(emoji="🔰", label="Verify", custom_id="Verification_verify")
    async def verify(self, _button: discord.ui.Button, interaction: discord.Interaction):
        member = interaction.user
        
        if self.unverified_role in member.roles:
            await interaction.response.send_modal(VerifyModal(self.unverified_role))
        else:
            await interaction.response.send_message("No need, you are already verified!", ephemeral=True)


class VerifyModal(discord.ui.Modal):
    def __init__(self, role):
        super().__init__(title="Verification")

        self.verify_word = choice(VERIFY_WORDS)
        self.unverified_role = role

        self.add_item(
            discord.ui.InputText(
                label=f"Please enter the word '{self.verify_word}'",
                placeholder=self.verify_word,
            )
        )

    async def callback(self, interaction: discord.Interaction):
        response = self.children[0].value
        # Clean the value
        response = response.lower().strip().replace(" ", "")

        if response == self.verify_word:
            # Remove unverified role
            member = interaction.user
            # This will trigger the removed role listener
            await member.remove_roles(self.unverified_role)

            await interaction.response.send_message("Successfully verified!", ephemeral=True)
        else:
            await interaction.response.send_message("Verification failed\n\nPlease try again:", view=VerifyButton(self.unverified_role), ephemeral=True)


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.unverified_role = None


    @commands.Cog.listener()
    async def on_ready(self):
        self.unverified_role = self.bot.get_guild(GUILD_ID).get_role(UNVERIFIED_ID)
        self.bot.add_view(VerifyButton(self.unverified_role))

        await self.retroactive_kick()
        
    @discord.message_command(name="Attach verification button")
    @discord.default_permissions(manage_messages=True)
    async def attach_verify(self, ctx: discord.ApplicationContext, message: discord.Message):
        """
        Attach the verification button to a message
        """
        if message.author.id != self.bot.user.id:
            await ctx.respond("The selected message must have been sent by the bot", ephemeral=True)
        else:
            await message.edit(view=VerifyButton(self.unverified_role))
            await ctx.respond("Attached", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Ignore bots
        if member.bot: return

        # If member has never been verified, give the unverified role
        if not await is_verified(member):
            await member.add_roles(self.unverified_role)


    @commands.Cog.listener()
    async def on_member_update(self, old: discord.Member, new: discord.Member):
        member = new
        if member.bot: return

        # Verification role removed
        if self.unverified_role in old.roles and self.unverified_role not in new.roles:
            # User has been verified so mark in db
            await set_prop(member.id, DB_COLL, "verified", True)

        # Role added
        elif self.unverified_role in new.roles and self.unverified_role not in old.roles:
            # If the user has already been verified just remove the role again
            if await is_verified(member):
                await member.remove_roles(self.unverified_role, reason="User already verified")
                return

            # If the user has already been in the server for lger than the verification period, also remove the role
            if (discord.utils.utcnow() - member.joined_at) > VERIFY_DURATION:
                await member.remove_roles(self.unverified_role, reason="User has already been in server for verification period")
                return

            # Dm the user telling them to verify
            try:
                timestamp = discord.utils.format_dt(discord.utils.utcnow() + VERIFY_DURATION, "t")
                await member.send(
                    f"Hey {member.mention}, welcome to {member.guild.name}!\n\n" 
                    f"To keep everyone safe from data scrapers and bots, we require all users to complete a quick CAPTCHA to remain in the server.\n" 
                    f"This must be completed by {timestamp} or you will be kicked from the server.\n\n" 
                    f"Please check out <#{VERIFY_ID}> for more information."
                )
            except discord.Forbidden:
                pass

            # Kick off the task to kick them :3
            asyncio.create_task(
                self.kick_task(member.id)
            )


    async def kick_task(self, member_id: int, delay: dt.timedelta = VERIFY_DURATION):
        # Wait the specified amount of time
        await asyncio.sleep(delay.total_seconds())
        await self.bot.wait_until_ready()

        # Check if user isn't already verified
        member = self.bot.get_guild(GUILD_ID).get_member(member_id)
        # If the user has the role, perform the kick
        if member and not member.bot and self.unverified_role in member.roles:
            # Try to dm the user about the kick
            try:
                await member.send(
                    f"Hey {member.mention}, unfortunately you have been kicked from {member.guild.name} for not verifying that you are a human :(\n\n"
                    f"Please feel free to rejoin, and make sure to check out <#{VERIFY_ID}> to stick around"
                )
            except discord.Forbidden:
                pass

            await member.kick(reason="Unverified")

    async def retroactive_kick(self):
        """Goes over the list of members with the unverified role and schedules tasks to kick users who have not verified"""
        for member in self.unverified_role.members:
            join_time = member.joined_at
            now = discord.utils.utcnow()

            time_since_join = now - join_time

            asyncio.create_task(
                self.kick_task(member.id, VERIFY_DURATION - time_since_join)
            )


def setup(bot):
    bot.add_cog(Verification(bot))
