import discord
from discord.ext import commands


class BadSubCommand(Exception):  # Used in command groups when the parent command can't be run automatically
    pass


class BotMember(commands.CommandError):  # Custom error for StrictMember
    pass
