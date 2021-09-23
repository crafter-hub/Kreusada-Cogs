import asyncio
import contextlib
import datetime
import json
import pathlib
from typing import List

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import warning
from redbot.core.utils.predicates import MessagePredicate

EMOJIS = {
    "christmas": "\N{CHRISTMAS TREE}",
    "halloween": "\N{JACK-O-LANTERN}",
    "get_well_soon": "\N{THERMOMETER}\N{VARIATION SELECTOR-16}",
    "birthday": "\N{PARTY POPPER}",
    "valentines": "\N{GROWING HEART}",
    "wedding": "\N{BRIDE WITH VEIL}\N{ZERO WIDTH JOINER}\N{FEMALE SIGN}\N{VARIATION SELECTOR-16}",
    "new_home": "\N{HOUSE WITH GARDEN}",
    "new_years": "\N{CLINKING GLASSES}",
    "confession": "\N{LOVE LETTER}",
    "birthday_invitation": "\N{FACE WITH PARTY HORN AND PARTY HAT}",
    "party_invitation": "\N{FIREWORKS}",
    "wedding_invitation": "\N{CHURCH}\N{VARIATION SELECTOR-16}",
}

with open(pathlib.Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]

class Emoji:
    def __init__(self, name, emoji):
        self.name = name
        self.emoji = emoji
        self.formatted_name = name.replace("_", " ").capitalize()
        if name in ["birthday_invitation", "wedding_invitation", "party_invitation"]:
            self.card_type_name = "invite"
        else:
            self.card_type_name = "card"


class SendCards(commands.Cog):
    """Send cards to other users."""

    __author__ = ["Kreusada"]
    __version__ = "2.0.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self.users_emoji = "\N{BUSTS IN SILHOUETTE}"
        self.card_plaque_emoji = "\U0001faa7"
        self.speech_balloon_emoji = "\N{SPEECH BALLOON}"
        self.airplane_emoji = "\N{AIRPLANE}\N{VARIATION SELECTOR-16}"
        self.question_mark_emoji = "\N{BLACK QUESTION MARK ORNAMENT}\N{VARIATION SELECTOR-16}"
        self.image_emoji = "\N{FRAME WITH PICTURE}\N{VARIATION SELECTOR-16}"
        self.emoji_list: List[Emoji] = list(map(lambda x: Emoji(*x), EMOJIS.items()))
        if 719988449867989142 in self.bot.owner_ids:
            with contextlib.suppress(RuntimeError, ValueError):
                self.bot.add_dev_env_value(self.__class__.__name__.lower(), lambda s: self)

    def cog_unload(self):
        with contextlib.suppress(KeyError):
            self.bot.remove_dev_env_value(self.__class__.__name__.lower())

    async def send_embed(self, ctx: commands.Context, content: str, step: int = None):
        embed = discord.Embed(
            description=content,
            color=await ctx.embed_colour(),
        )
        if step is not None:
            embed.set_footer(text=f"Step {step}/3 | " + "Type \"stop()\" to discontinue the interactive session.")
        if await ctx.embed_requested():
            return await ctx.send(embed=embed)
        else:
            return await ctx.send(content)

    async def edit_embed(self, message: discord.Message, content: str):
        if (embeds := message.embeds):
            embed = embeds[0].to_dict()
            embed = message.embeds[0].to_dict()
            embed["description"] = content
            await message.edit(embed=discord.Embed.from_dict(embed))
        else:
            await message.edit(content=content)

    @commands.command()
    async def sendcard(self, ctx: commands.Context):
        """Send a card to a user.
        Run the command to open an interactive session where you can
        provide input in a more comfortable way.
        """
        enum = list(enumerate(self.emoji_list, start=1))
        enum_dict = dict(enum)
        td = lambda x: f"{x} " if x < 10 else x
        message = "\n".join(f"`{td(c)}:` {v.emoji} {v.formatted_name}" for c, v in enum)
        await self.send_embed(
            ctx,
            f"{self.card_plaque_emoji} **Card/Invite Selection**\n\n"
            "Find the card that you want, and send the number.\n\n" + message,
            1,
        )
        pred = MessagePredicate.contained_in(list(map(str, range(1, len(enum) + 1))) + ["stop()"])
        try:
            card_type = await self.bot.wait_for("message", check=pred, timeout=40)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to send, please start over.")
            return
        if card_type.content.lower() == "stop()":
            await ctx.send("Stopping.")
            return

        card_type = enum_dict[int(card_type.content)]
        qualified_name = card_type.formatted_name.lower()
        if card_type.card_type_name == "card":
            qualified_name += " " + card_type.card_type_name

        await self.send_embed(
            ctx,
            f"{self.users_emoji} **Recipient Information**\n\n"
            "Who would you like to send this card to? "
            "Please provide a user ID, their name, name and discriminator, or "
            "their mention.",
            2,
        )
        check = lambda x: x.channel == ctx.channel and x.author == ctx.author
        try:
            user = await self.bot.wait_for("message", check=check, timeout=40)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to send, please start over.")
            return
        else:
            if user.content.lower() == "stop()":
                await ctx.send("Stopping.")
                return
            try:
                user_converter = commands.UserConverter()
                user_object = await user_converter.convert(ctx, user.content)
            except commands.UserNotFound:
                await ctx.send(
                    "Failed to get user information from your message, please start over."
                )
                return

        await self.send_embed(
            ctx,
            f"{self.speech_balloon_emoji} **Message Content**\n\n"
            f"Now you should send the message to go in your {qualified_name}.\n\n"
            f"{self.image_emoji} **Image Attachments**\n\n"
            f"Attaching an image alongside your message will add an image to your {card_type.card_type_name}.",
            3,
        )

        try:
            message = await self.bot.wait_for("message", check=check, timeout=40)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to send, please start over.")
            return
        else:
            if message.content.lower() == "stop()":
                await ctx.send("Stopping.")
                return
            loading_message = await self.send_embed(
                ctx, "\N{HOURGLASS}\N{VARIATION SELECTOR-16} **Loading...**"
            )

        kwargs = {}

        if message.attachments:
            attachment = await message.attachments[0].to_file()
            kwargs["file"] = attachment

        embed = discord.Embed(
            title=f"{card_type.emoji} {qualified_name.title()} from {ctx.author}!",
            description=message.content,
            color=await ctx.embed_colour(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )

        if kwargs.get("file"):
            embed.set_image(url="attachment://" + str(attachment.filename))

        kwargs["embed"] = embed

        try:
            await user_object.send(**kwargs)
        except discord.HTTPException:
            await ctx.send(
                warning(
                    f"Failed to send this {qualified_name} to {user_object}. Sorry!"
                )
            )
        else:
            await self.edit_embed(
                loading_message,
                f"**{self.airplane_emoji} {qualified_name.title()} Successfully Sent**\n\n"
                f"The {qualified_name} was successfully sent and is now waiting to be opened "
                "by the recipient.",
            )
