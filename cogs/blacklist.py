import discord
from discord.utils import get
from discord.ext import commands
import re


def run_blacklist(text):
    text = re.sub(r"[*_`~]", "", text)  # get rid of markdown

    with open("./word_blacklist.txt", "r") as fd:  # open blacklist file
        for i in fd.readlines():
            i = i.rstrip()  # stick all the blacklist rules in
            if re.search(fr"\b{i}\b", text, re.IGNORECASE):  # if that is a match
                return re.sub(fr"\b{i}\b", r"**\g<0>**", text, re.IGNORECASE)
    return False


class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if run_blacklist(message.content):
            await message.delete()
            await message.channel.send(f"{message.author.mention} Please be respectful and read the rules."
                                       , delete_after=5)


def setup(bot):
    bot.add_cog(Blacklist(bot))
