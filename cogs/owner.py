import discord
from discord.ext import commands
import ast

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


async def autocomplete_cogs(ctx: discord.AutocompleteContext):
    return [x[5:] for x in ctx.bot.extensions.keys()]


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command()
    @discord.default_permissions(manage_guild=True)
    async def reload(self, ctx: discord.ApplicationContext,
                     cog: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(autocomplete_cogs))):
        """
        Applies changes to a loaded cog
        """
        try:
            self.bot.reload_extension("cogs." + cog)
            self.bot.dispatch("load", cog)
        except Exception as error:
            await ctx.send(f"```py\n{error}```")
            return
        await ctx.respond("✅")
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
            cmd = "\n    ".join(code.splitlines())

            # wrap in async def body
            body = f"async def {fn_name}():\n    {cmd}"

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

            result = str(await eval(f"{fn_name}()", env))

            output = f"```py\n>>> {code}\n\n\n{result}```"

            if len(output) > 2000:
                await ctx.send("The output is too long?")
            else:
                await ctx.send(output)
        except Exception as e:
            await ctx.send(f"```py\n>>> {code}\n\n\n{e}```")
            raise e


def setup(bot):
    bot.add_cog(Owner(bot))
