import discord
from discord.ext import commands
from config import RED, STAFF_CMD_ID
from utils import utc_now
import re
import datetime as dt


class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blacklist = []

        with open("./blacklist.txt", "r") as fd:  # open blacklist file
            for i in fd.readlines():
                self.blacklist.append(i.rstrip())  # stick all the blacklist rules in

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        content = message.content
        text = re.sub(r"[*_`~]", "", content)  # get rid of markdown

        tripped = False
        for rule in self.blacklist:
            if re.search(fr"\b{rule}\b", text, re.IGNORECASE):  # if that is a match
                text = re.sub(fr"\b{rule}\b", r"**\g<0>**", text, re.IGNORECASE)
                tripped = True
                break  # If we find a slur, don't bother with the rest of the list

        if tripped:
            await message.delete()
            if not message.author.bot:
                # 5 second mute to discourage spam
                try:
                    await message.author.timeout_for(dt.timedelta(seconds=5))
                except discord.Forbidden:
                    pass

                await message.channel.send(f"{message.author.mention} Please be respectful and read the rules.",
                                           delete_after=5)

                em = discord.Embed(colour=RED)
                em.description = f"**Message by {message.author.mention} auto-deleted in " \
                                 f"{message.channel.mention}**\n{text}"
                em.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
                em.set_footer(text=f"User ID: {message.author.id}")
                em.timestamp = utc_now()
                await self.bot.get_channel(STAFF_CMD_ID).send(embed=em)


def setup(bot):
    bot.add_cog(Blacklist(bot))
