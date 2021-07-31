import asyncio
import contextlib
import io
import pathlib
import random
import re

import discord
import gtts
import yaml
from redbot.core import commands
from redbot.core.commands import BadArgument, Context, Converter
from redbot.core.utils.chat_formatting import bold, humanize_list

QUESTION = "\N{WHITE QUESTION MARK ORNAMENT}"


class Difficulty(Converter):
    async def convert(self, ctx: Context, argument: str.lower):
        difficulties = ("easy", "medium", "hard")
        if argument not in difficulties:
            raise BadArgument(
                "Difficulty must be one of {}.".format(humanize_list(difficulties, style="or"))
            )
        return argument


def get_clue(s):
    r = random.randrange  # shorttyping
    firstfind = re.findall(s[len(s)//r(4, 6):len(s)-1//1-len(s)//r(3, 4)], s)
    return re.sub(firstfind[0], "_" * len(firstfind[0]), s)


class SpellingBee(commands.Cog):
    """Test your spelling skills with text-to-speech questions."""

    def __init__(self, bot):
        self.bot = bot
        with open(pathlib.Path(__file__).parent / "data.yml") as f:
            self.data = yaml.full_load(f)["words"]
        self.spelling_messages = {}

    @commands.command()
    async def spell(self, ctx, difficulty: Difficulty):
        """Try and spell a word."""
        alert = await ctx.send("Loading spelling test...")
        word, example = random.choice(list(self.data[difficulty].items()))
        mp3 = io.BytesIO()
        tts = gtts.gTTS(f"{word}... {example}")
        tts.write_to_fp(mp3)
        mp3.seek(0)
        kwargs = {
            "content": (
                "Listen to the audio carefully and write down the correct"
                " spelling of the word that is being played out to you.\n"
                "You have **40** seconds to answer.\nThe word will be read "
                "followed by an example of the word in a sentence.\n\n"
                f"Hit the {QUESTION} reaction for a small clue."
            ),
            "file": discord.File(mp3, "spell_test.mp3"),
        }
        with contextlib.suppress(discord.NotFound):
            await alert.delete()
        msg = await ctx.send(**kwargs)
        self.spelling_messages[word] = [ctx.author.id, msg.id]
        await msg.add_reaction(QUESTION)

        def check(x):
            return x.author == ctx.author and x.channel == ctx.channel

        try:
            answer = await self.bot.wait_for("message", check=check, timeout=40)
        except asyncio.TimeoutError:
            message = "You took too long! The correct spelling was {}.".format(bold(word))
        else:
            answer = answer.content.lower()
            if answer == word:
                message = "Correct! {}".format("\N{PARTY POPPER}")
            else:
                message = "Not quite. The correct spelling was {}.".format(bold(word))
        finally:
            await ctx.send(message)
            del self.spelling_messages[word]

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        message = reaction.message

        if user.bot:
            return
        if not user.guild:
            return

        if reaction.emoji != QUESTION:
            return

        if await self.bot.cog_disabled_in_guild(self, user.guild):
            return

        if not await self.bot.ignored_channel_or_guild(message):
            return

        if not await self.bot.allowed_by_whitelist_blacklist(user):
            return

        for k, v in self.spelling_messages.items():
            if all([user.id == v[0], message.id == v[1], not message.content.endswith("||")]):
                await reaction.message.edit(
                    content=f"{message.content}\n\n**Clue:** ||{get_clue(k)}||"
                )


def setup(bot):
    bot.add_cog(SpellingBee(bot))
