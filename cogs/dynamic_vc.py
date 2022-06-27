import discord
from discord.ext import commands
from config import DYN_VC_ID


class DynamicVC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channels = []  # all temp VCs

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member,
                                    before: discord.VoiceState, after: discord.VoiceState):
        # If the user joins a channel
        if before.channel != after.channel and after.channel:
            # if they join the DVC channel
            if after.channel.id == DYN_VC_ID:
                # Duplicate the channel to retain permissions and parent - set name
                vc = await after.channel.category.create_voice_channel(name="Temp Voice")
                self.channels.append(vc.id)  # save the ID
                await member.move_to(vc)

        # if they left a voice channel we made
        if before.channel and before.channel.id in self.channels:
            if len(before.channel.members) == 0:  # if channel is empty
                self.channels.remove(before.channel.id)  # remove channel from DynVC list
                await before.channel.delete()  # delete the actual channel


def setup(bot):
    bot.add_cog(DynamicVC(bot))
