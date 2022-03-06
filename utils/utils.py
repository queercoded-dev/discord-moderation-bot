from math import ceil

import discord
from discord.ext import commands
import re
import datetime as dt

LETTERS = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯", "🇰", "🇱", "🇲", "🇳", "🇴", "🇵", "🇶", "🇷",
           "🇸", "🇹", "🇺", "🇻", "🇼", "🇽", "🇾", "🇿"]


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def chunks(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class Page(discord.ui.View):
    """
    A UI view that lets you scroll through pages
    """

    def __init__(self, ctx: commands.Context, pages: list, index: int = 0, footer: str = None):
        super().__init__()

        self.pages = pages
        self.index = index
        self.ctx = ctx
        self.footer = footer
        self.max_page = len(pages)

    def set_embed_footer(self, embed: discord.Embed):
        text = f"Page {self.index + 1} of {self.max_page}"
        if self.footer:
            text = self.footer + "\n" + text

        embed = embed.set_footer(text=text, icon_url=embed.footer.icon_url)
        return embed

    async def update(self, interaction: discord.Interaction):
        embed = self.pages[self.index]
        embed = self.set_embed_footer(embed)
        await interaction.response.edit_message(embed=embed)

    # Interaction stuff

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id == self.ctx.author.id:
            return True
        else:
            await interaction.response.send_message(content="Run this command yourself to see more pages",
                                                    ephemeral=True)
            return False

    @discord.ui.button(emoji="⏮️")
    async def first_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.index != 0:
            self.index = 0
            await self.update(interaction)

    @discord.ui.button(emoji="◀️")
    async def prev_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.index -= 1
        if self.index < 0:
            self.index = self.max_page - 1
        await self.update(interaction)

    @discord.ui.button(emoji="▶️")
    async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.index += 1
        if self.index >= self.max_page:
            self.index = 0
        await self.update(interaction)

    @discord.ui.button(emoji="⏭️")
    async def last_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        new_index = self.max_page - 1
        if self.index != new_index:
            self.index = new_index
            await self.update(interaction)

    async def on_timeout(self):
        try:
            self.stop()
        except discord.NotFound:
            pass


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
