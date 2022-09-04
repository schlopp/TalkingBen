import random
import textwrap
import io
import asyncio
import contextlib
import traceback
import re
from datetime import datetime, timedelta
from typing import Dict


import discord  # type: ignore
import toml
import discord
from discord.ext import commands  # type: ignore


@commands.command(name="help")
async def _help(ctx: commands.Context):
    await ctx.send("Create a channel named `talking-ben` to use me")
    await ctx.send(
        "https://tenor.com/view/talking-ben-talking-tom-ben-talking-ben-no-gif-25034220"
    )

intents = discord.Intents.default()
intents.messages = True
intents.typing = True


typing_guilds: Dict[int, datetime] = {}


bot = commands.Bot("tb ", intents=intents, owner_ids=[393305855929483264])


bot.remove_command("help")
bot.add_command(_help)


@bot.event
async def on_ready():
    print("ready!")


@bot.listen("on_typing")
async def ben_response(channel: discord.TextChannel, user: discord.User, when: datetime):
    if "talking-ben" in channel.name:
        if not typing_guilds.get(channel.id) or typing_guilds[channel.id] < datetime.now():
            await channel.send("Ben?")
        typing_guilds[channel.id] = when + timedelta(minutes=1)


@bot.listen("on_message")
async def question_response(message: discord.Message) -> None:
    if not isinstance(message.channel, discord.TextChannel):
        return
    if not isinstance(message.channel.name, str):
        return
    if "talking-ben" not in message.channel.name:
        return
    if message.author.bot:
        return

    await message.channel.send(
        random.choice(["Yeees?", "No.", "Ho ho ho!", "Eugh.."]), mention_author=False
    )


def clean_code(code: str):
    if re.search(r"^```(.|\s)*```$", code):
        return code.split("\n", 1)[1].strip()[:-3]
    if re.search(r"^`.*`$", code):
        return code.strip()[1:-1]
    return code.strip()


@bot.command(name="eval", aliases=["ev", "exec", "execute"])
@commands.is_owner()
async def _eval(ctx: commands.Context, *, code: str) -> None:
    start_time = datetime.now()
    code = clean_code(code)
    local_variables = {
        "discord": discord,
        "commands": commands,
        "bot": bot,
        "channel": ctx.channel,
        "guild": ctx.guild,
        "author": ctx.author,
        "ctx": ctx,
        "asyncio": asyncio,
    }
    stdout = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout):
            exec(f"async def func():\n{textwrap.indent(code, '    ')}", local_variables)

            obj = await local_variables["func"]()
            result = f"{stdout.getvalue()}\n-- {obj}"
    except Exception as e:
        result = f"{traceback.format_exc()}\n\n{e}"

    time_passed = datetime.now() - start_time
    if len(result) > 1500:
        txtfile = io.StringIO()
        txtfile.write(result)
        txtfile.seek(0)
        return await ctx.send(
            f"Executed in **{round(time_passed.total_seconds(), 3)}** seconds.",
            file=discord.File(txtfile, "result.py"),  # type: ignore
        )

    await ctx.send(
        f"Executed in **{round(time_passed.total_seconds(), 3)}** seconds.",
        embed=discord.Embed(description=f"```py\n{result}```"),
    )


@bot.command()
async def status(ctx, *, informationthatineed):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if not is_owner:
        return
    message = ctx.message
    if informationthatineed == "normal":
        await bot.change_presence(activity=discord.Game(name=f"Yeees? - tb help"))
        await message.add_reaction("👌")
        return
    await bot.change_presence(activity=discord.Game(name=informationthatineed))
    await message.add_reaction("👌")


config = toml.load("config.toml")
bot.run(config["token"])
