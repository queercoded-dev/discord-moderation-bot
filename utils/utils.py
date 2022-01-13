from math import ceil

import discord
from discord.ext import commands
import re
import datetime as dt


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def chunks(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class PageView(discord.ui.View):
    def __init__(self, page, ctx: commands.Context):
        super().__init__()
        self.page = page  # type: Page
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id == self.ctx.author.id:
            return True
        else:
            await interaction.response.send_message(content="Run this command yourself to see more pages",
                                                    ephemeral=True)
            return False

    async def on_timeout(self):
        await self.page.stop()

    @discord.ui.button(emoji="⏮️")
    async def first(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.page.first_page()

    @discord.ui.button(emoji="◀️")
    async def back(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.page.prev_page()

    @discord.ui.button(emoji="▶️")
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.page.next_page()

    @discord.ui.button(emoji="⏭️")
    async def last(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.page.last_page()


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
            await self.msg.edit(content="`Page menu is locked`", view=None)
        except discord.NotFound:
            pass

    async def start(self):
        if len(self.pages) > 1:
            await self.update()
            await self.msg.edit(view=PageView(self, self.ctx))  # Add the pages


def pos_int(digit: str):
    """Ensures the input is a positive integer"""
    if digit.isdigit() and int(digit) > 0:
        return int(digit)
    raise commands.BadArgument


class RelativeTime(commands.Converter):
    """An argument converter to match relative time, e.g. 1h 30m
    Returns the total amount of time in minutes"""

    async def convert(self, ctx, argument):
        rex = re.findall(r"\b(?:([1-9][0-9]{0,4}(?:[.,][1-9]{1,2})?)([dhm]))+\b", argument, re.IGNORECASE)
        if rex:
            total = 0
            for num, unit in rex:
                num = float(num)

                if unit == "h":
                    num *= 60  # if in hours, convert to minutes
                elif unit == "d":
                    num *= 1440
                total += num
            return total
        else:
            raise commands.BadArgument


def format_time(time: dt.timedelta, *args):
    """
    Convert timedelta into something readable
    """
    f_time = {}  # this will store our days, hours, minutes, seconds
    time = ceil(time.total_seconds())
    f_time["day"], remainder = divmod(time, 86400)  # get days as a whole number
    f_time["hour"], remainder = divmod(remainder, 3600)  # etc
    f_time["minute"], f_time["second"] = divmod(remainder, 60)

    output = ""
    for unit, value in f_time.items():  # iterate through
        # Ignore values if they are 0 and handle plurals
        if unit not in args:
            if value == 1:
                output += f"{int(value)} {unit}, "
            elif value > 1:
                output += f"{int(value)} {unit}s, "

    if not output and args:
        output = f"0 {list(f_time)[-len(args) - 1]}s, "

    return output[:-2]  # cut off the final ", "
