import discord
from discord.ext import commands
import ast
from config import GREEN
from typing import Optional

# These imports are just for the run command, for convenience
import datetime as dt
import re
import config
from utils import *


def insert_returns(body):
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the or else
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, cog: str):
        """
        Reloads a cog and updates changes to it
        """
        try:
            self.bot.reload_extension("cogs." + cog)
            self.bot.dispatch("load", cog)
        except Exception as error:
            await ctx.send(f"```py\n{error}```")
            return
        await ctx.send("✅")
        print(f"------------Reloaded {cog}------------")

    @commands.command()
    @commands.is_owner()
    async def run(self, ctx, *, code: str):
        """
        Run python stuff
        """
        fn_name = "_eval_expr"

        code = code.strip("` ")  # get rid of whitespace and code blocks
        if code.startswith("py\n"):
            code = code[3:]

        try:
            # add a layer of indentation
            cmd = "\n    ".join(f"    {i}" for i in code.splitlines())

            # wrap in async def body
            body = f"async def {fn_name}():\n{cmd}"

            parsed = ast.parse(body)
            body = parsed.body[0].body

            insert_returns(body)

            env = {
                'bot': self.bot,
                'ctx': ctx,
                'message': ctx.message,
                'server': ctx.message.guild,
                'channel': ctx.message.channel,
                'author': ctx.message.author,
                'commands': commands,
                'discord': discord,
                'guild': ctx.message.guild,
            }
            env.update(globals())

            exec(compile(parsed, filename="<ast>", mode="exec"), env)

            result = (await eval(f"{fn_name}()", env))

            out = ">>> " + code + "\n"
            output = "```py\n{}\n\n{}```".format(out, result)

            if len(output) > 2000:
                await ctx.send("The output is too long?")
            else:
                await ctx.send(output.format(result))
        except Exception as e:
            await ctx.send("```py\n>>> {}\n\n\n{}```".format(code, e))

    @commands.command(aliases=["osem"])
    @commands.is_owner()
    async def oneshot_embed(self, ctx, channel: discord.TextChannel,
                            colour: Optional[discord.Colour], title, *, description):
        """
        Quick embed t.osem <channel> #<colour?> "<title>" <description>(*)
        """
        title = str.strip(title)
        embed = discord.Embed(title=title, description=description, colour=colour if colour else GREEN)
        embed.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.timestamp = dt.datetime.utcnow()
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Owner(bot))
