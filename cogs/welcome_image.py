from discord.ext import commands
import discord
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from config import GUILD_ID, WELCOME_IMAGE_ID

WELCOME_BG = "./Join.png"
LEAVE_BG = "./Leave.png"
FONT = "FreeMonoBold.ttf"


def draw_text(x: int, y: int, font: ImageFont, text: str, draw: ImageDraw):
    """
    Draw text on an image
    y is the y pos the image will be placed under
    font is the TrueType font
    text is the text to be drawn
    draw is the ImageDraw object
    width is the width of the image to be drawn on - the text will be centered in this width
    """
    shadow_color = (0, 0, 0)
    fill_color = (255, 255, 255)
    for y_offset in range(-1, 2):
        for x_offset in range(-1, 2):
            draw.text((x + x_offset, y + y_offset), text, font=font, fill=shadow_color)
    draw.text((x, y), text, font=font, fill=fill_color)
    return draw


def num_suffix(n):
    """
    Format a number into a string and prepend "nd" "st" "rd" etc
    """
    return str(n) + ("th" if 4 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


def make_welcome(pfp: BytesIO, member: discord.Member):
    tag = str(member)  # username#1234
    joinpos = member.guild.member_count

    bg = Image.open(WELCOME_BG)  # open the welcome background
    bg = bg.resize((1024, 415))  # resize

    pfp = Image.open(pfp)  # make the pfp a PIL Image
    pfp = pfp.resize((265, 265))  # make pfp 265x265

    # hardcode values since the images are resized to a hardcoded value
    bg.paste(pfp, (75, 75, 340, 340), pfp)  # paste pfp onto image

    draw = ImageDraw.Draw(bg)  # Start a draw canvas using the background

    # draw all text
    font = ImageFont.truetype(FONT, 60)
    draw = draw_text(365, 75, font, "Welcome,", draw)
    font = ImageFont.truetype(FONT, 40)
    draw = draw_text(365, 155, font, tag, draw)
    font = ImageFont.truetype(FONT, 36)
    draw = draw_text(365, 220, font, f"You are our {num_suffix(joinpos)} member!", draw)
    font = ImageFont.truetype(FONT, 60)
    draw = draw_text(365, 270, font, "_", draw)

    return bg  # changes are saved to the bg so return that


def make_leave(pfp: BytesIO, member: discord.Member):
    tag = str(member)  # username#1234
    join_pos = member.guild.member_count

    bg = Image.open(LEAVE_BG)  # open the goodbye background
    bg = bg.resize((1024, 415))  # resize

    pfp = Image.open(pfp)  # make the pfp a PIL Image
    pfp = pfp.resize((265, 265))  # make pfp 265x265

    # hardcode values since the images are resized to a hardcoded value
    bg.paste(pfp, (75, 75, 340, 340), pfp)  # paste pfp onto image

    draw = ImageDraw.Draw(bg)  # Start a draw canvas using the background

    font = ImageFont.truetype(FONT, 60)
    draw = draw_text(365, 75, font, "Goodbye,", draw)
    font = ImageFont.truetype(FONT, 40)
    draw = draw_text(365, 155, font, tag, draw)
    font = ImageFont.truetype(FONT, 36)
    draw = draw_text(365, 220, font, f"We now have {join_pos} members.", draw)
    font = ImageFont.truetype(FONT, 60)
    draw = draw_text(365, 270, font, "_", draw)

    return bg  # changes are saved to the bg so return that


class WelcomeImage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: commands.Bot

    async def get_pfp(self, member: discord.Member):
        """
        Downloads profile picture as a PNG into a bytes object
        """
        img = member.display_avatar
        img = await img.read()
        return img

    async def send_image(self, image, filename="image.png"):
        """
        Convert the image object to a bytes stream and sends it to the needed channel
        """
        image_b = BytesIO()
        image.save(image_b, format='png')
        image_b.seek(0)

        channel = self.bot.get_channel(WELCOME_IMAGE_ID)
        await channel.send(file=discord.File(image_b, filename=filename))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return
        image = await self.get_pfp(member)
        image = make_welcome(BytesIO(image), member)
        await self.send_image(image)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return
        image = await self.get_pfp(member)
        image = make_leave(BytesIO(image), member)
        await self.send_image(image)


def setup(bot):
    bot.add_cog(WelcomeImage(bot))
