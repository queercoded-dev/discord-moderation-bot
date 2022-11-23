import discord
from discord.ext import commands
from config import GUILD_ID, SOBBOARD_ID, MAIN
from utils.db_utils import find_docs, insert_doc

STAR = "😭"
STAR_THRESHOLD = 5

STAR_CONTENT = "😭 {count} | Message in {channel} by {author} had us sobbing"


def message_to_embed(message: discord.Message):
    em = discord.Embed(colour=MAIN, timestamp=message.created_at, description=message.content)
    em.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
    em.add_field(name="Details", value=f"[LINK]({message.jump_url})")

    if message.attachments:
        attachment = message.attachments[0]
        if attachment.content_type in ["image/jpeg", "image/png"]:
            em.set_image(url=attachment.url)
        else:
            em.set_footer(text="📎 Some attachments could not be shown")

    if message.reference:
        reply_url = message.reference.jump_url
        em.description = f"> [Reply]({reply_url})\n" + em.description

    return em


class Sobboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # type: commands.Bot

    async def try_message(self, channel_id: int, message_id: int):
        # Search the cache for that message
        cached = discord.utils.get(self.bot.cached_messages, channel__id=channel_id, id=message_id)
        if not cached:
            try:
                message = await self.bot.get_channel(channel_id).fetch_message(message_id)
            except discord.NotFound:
                return None
            else:
                return message
        else:
            return cached

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not payload.guild_id or payload.guild_id != GUILD_ID:
            return
        if str(payload.emoji) != STAR:
            return
        if payload.channel_id == SOBBOARD_ID:  # Ignore the sobboard channel ofc
            return

        message = await self.try_message(payload.channel_id, payload.message_id)
        if not message:  # Shouldn't happen tbh
            return

        stars = discord.utils.get(message.reactions, emoji=STAR)
        if not stars:  # Also shouldn't happen
            return

        entry = await find_docs("sobboard",
                                {"channel": str(payload.channel_id), "message": str(payload.message_id)}, 1)
        entry = entry[0] if entry else None

        if entry:
            destination = entry["destination"]
            star_msg = await self.try_message(SOBBOARD_ID, int(destination))
            if not star_msg:  # If message has been deleted, ignore it
                return

            await star_msg.edit(content=STAR_CONTENT.format(count=stars.count,
                                                            channel=message.channel.mention,
                                                            author=message.author.mention))

        elif stars.count >= STAR_THRESHOLD:  # Enough stars to make a new entry
            channel = self.bot.get_channel(SOBBOARD_ID)
            star_msg = await channel.send(
                STAR_CONTENT.format(count=stars.count, channel=message.channel.mention, author=message.author.mention),
                embed=message_to_embed(message)
            )

            await insert_doc("sobboard", {
                "channel": str(message.channel.id),
                "message": str(message.id),
                "destination": str(star_msg.id),
            })


def setup(bot):
    bot.add_cog(Sobboard(bot))
