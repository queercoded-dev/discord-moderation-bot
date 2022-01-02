import discord
from discord.ext import commands
from asyncio import TimeoutError
from datetime import timedelta
import datetime as dt
from math import ceil


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


nav_emotes = ["⏮️", "◀️", "▶️", "⏭️"]


class Page:
    """
    A class to create a scrollable menu
    """

    def __init__(self, ctx: commands.Context, msg: discord.Message, pages: list, footer: str = None):
        self.pages = pages
        self.index = 0
        self.ctx = ctx
        self.msg = msg
        self.max_page = len(pages)
        self.footer = footer

    def _set_embed_footer(self, embed: discord.Embed):
        text = f"Page {self.index + 1} of {self.max_page}"
        if self.footer:
            text = self.footer + "\n" + text

        embed = embed.set_footer(text=text, icon_url=embed.footer.icon_url)
        return embed

    async def update(self):
        embed = self.pages[self.index]
        embed = self._set_embed_footer(embed)
        await self.msg.edit(embed=embed)

    async def first_page(self):
        self.index = 0
        await self.update()

    async def last_page(self):
        self.index = self.max_page - 1
        await self.update()

    async def next_page(self):
        self.index += 1
        if self.index >= self.max_page:
            self.index = 0
        await self.update()

    async def prev_page(self):
        self.index -= 1
        if self.index < 0:
            self.index = self.max_page - 1
        await self.update()

    async def stop(self):
        try:
            await self.msg.clear_reactions()
            await self.msg.edit(content="`Page menu is locked`")
        except discord.NotFound:
            pass

    async def setup(self):
        for i in nav_emotes:
            try:
                await self.msg.add_reaction(i)
            except discord.NotFound:
                return

    def _check(self, r, user):
        return user.id == self.ctx.author.id and str(r) in nav_emotes and self.msg.id == r.message.id

    async def start(self):
        if len(self.pages) > 1:
            await self.update()
            await self.setup()
            while 1:
                try:
                    react, user = await self.ctx.bot.wait_for("reaction_add", timeout=60, check=self._check)
                    await self.msg.remove_reaction(react, user)
                except TimeoutError:
                    break

                if str(react) == nav_emotes[0]:
                    await self.first_page()
                elif str(react) == nav_emotes[1]:
                    await self.prev_page()
                elif str(react) == nav_emotes[2]:
                    await self.next_page()
                elif str(react) == nav_emotes[3]:
                    await self.last_page()

            await self.stop()


def short_time(time):
    """
    Convert a timedelta into a simple "1h 5m" style representation
    """
    if not isinstance(time, int) and not isinstance(time, float):
        return "None"

    time = timedelta(seconds=time)

    secs = time.total_seconds()
    days, secs = divmod(secs, 86400)
    hrs, secs = divmod(secs, 3600)
    mins, secs = divmod(secs, 60)
    secs = ceil(secs)
    o = ""
    if days:
        o += f"{days:.0f}d "
    if hrs:
        o += f"{hrs:.0f}h "
    if mins:
        o += f"{mins:.0f}m "
    if secs or not o:  # If seconds is 0, we will only append it if the string is blank
        o += f"{secs:.0f}s"
    if o.endswith(" "):
        o = o[:-1]
    return o


class BadSubCommand(Exception):  # Used in command groups when the parent command can't be run automatically
    pass


class BotMember(commands.CommandError):  # Custom error for StrictMember
    pass
