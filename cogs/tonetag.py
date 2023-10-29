import discord
from discord.ext import tasks, commands
import aiohttp
import re

TAG_ENDPOINT = "https://tonetag.is/api/list"
TAG_REGEX = r"(?:^|[\s|([{*~`])[/\\]([a-z]+)\b"


class ToneTag(discord.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: discord.Bot

        self.tags = []
        self.fetch_tags.start()

    @tasks.loop(count=1)
    async def fetch_tags(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(TAG_ENDPOINT) as response:
                if response.ok:
                    self.tags = await response.json()
                else:
                    print("Unable to fetch tone tags")

    @discord.message_command(name="View tone tags")
    async def view_tonetags(self, ctx: discord.ApplicationContext, message: discord.Message):
        """
        View details on tone tags in a message
        """
        tonetags = list(re.finditer(TAG_REGEX, message.content, re.IGNORECASE))

        if not tonetags:
            await ctx.respond("No tone tags detected", ephemeral=True)
            return

        tonetags = set([tag.group(1) for tag in tonetags])

        embeds = []
        for tonetag in tonetags:
            for tag in self.tags:
                if tag["tag"] == tonetag or tonetag in tag["aliases"] or tonetag in tag["hiddenAliases"]:
                    em = discord.Embed()
                    em.colour = await commands.ColourConverter().convert(None, tag["colour"])
                    em.title = tag["definition"] + " " + tag["emoji"][0]
                    em.description = tag["description"]
                    em.url = "https://tonetag.is/" + tag["tag"]
                    em.set_author(name="/" + tonetag)

                    embeds.append(em)

                    break

        if embeds:
            await ctx.respond(embeds=embeds, ephemeral=True)
        else:
            await ctx.respond("No tone tags detected", ephemeral=True)


def setup(bot):
    bot.add_cog(ToneTag(bot))
