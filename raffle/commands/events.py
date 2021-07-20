import asyncio
import contextlib
import random

import discord
from redbot.core import commands
from redbot.core.commands import Context
from redbot.core.i18n import Translator
from redbot.core.utils.chat_formatting import humanize_list, pagify

from ..mixins.abc import RaffleMixin
from ..mixins.metaclass import MetaClass
from ..utils.converters import RaffleExists, RaffleFactoryConverter
from ..utils.exceptions import DeniedUserEntryError
from ..utils.parser import RaffleManager
from ..utils.safety import RaffleSafeMember

_ = Translator("Raffle", __file__)


class EventCommands(RaffleMixin, metaclass=MetaClass):
    """All the raffle event leading commands."""

    @commands.group()
    async def raffle(self, ctx: Context):
        pass

    @raffle.command()
    async def draw(self, ctx: Context, raffle: RaffleFactoryConverter):
        """Draw a raffle and select a winner.

        **Arguments:**
            - `<raffle>` - The name of the raffle to draw a winner from.
        """
        async with self.config.guild(ctx.guild).raffles() as r:

            raffle_data = r.get(raffle, None)
            raffle_entities = lambda x: raffle_data.get(x, None)

            if not raffle_entities("entries"):
                return await ctx.send(_("There are no participants yet for this raffle."))

            winner = random.choice(raffle_entities("entries"))

            message = raffle_entities("end_message")
            if message:
                if isinstance(message, list):
                    message = random.choice(message)
            else:
                message = _(r"Congratulations {winner.mention}, you have won the {raffle} raffle!")

            on_end_action = raffle_entities("on_end_action") or "keep_winner"
            message = message.format(
                winner=RaffleSafeMember(self.bot.get_user(winner), "winner"), raffle=raffle
            )

            # Let's add a bit of suspense, shall we? :P
            await ctx.send(_("Picking a winner from the pool..."))
            await ctx.trigger_typing()
            await asyncio.sleep(raffle_data.get("suspense_timer", 2))

            await ctx.send(message)

            if on_end_action == "remove_winner":
                raffle_entities("entries").remove(winner)
            elif on_end_action == "keep_winner":
                pass
            elif on_end_action == "remove_and_prevent_winner":
                raffle_entities("entries").remove(winner)
                if raffle_entities("prevented_users"):
                    raffle_entities("prevented_users").append(winner)
                else:
                    raffle_data["prevented_users"] = [winner]
            else:
                # end
                r.pop(raffle)

        await self.clean_guild_raffles(ctx)

    @raffle.command()
    async def kick(self, ctx: Context, raffle: RaffleFactoryConverter, member: discord.Member):
        """Kick a member from your raffle.

        **Arguments:**
            - `<raffle>` - The name of the raffle.
            - `<member>` - The member to kick from the raffle.
        """
        async with self.config.guild(ctx.guild).raffles() as r:

            raffle_data = r.get(raffle, None)
            raffle_entities = lambda x: raffle_data.get(x)

            if member.id not in raffle_entities("entries"):
                return await ctx.send(_("This user has not entered this raffle."))

            raffle_entities("entries").remove(member.id)
            await ctx.send(_("User removed from the raffle."))

        await self.clean_guild_raffles(ctx)

    @raffle.command()
    async def join(self, ctx: Context, raffle: RaffleExists):
        """Join a raffle.

        **Arguments:**
            - `<raffle>` - The name of the raffle to join.
        """
        r = await self.config.guild(ctx.guild).raffles()

        try:
            RaffleManager.check_user_entry(ctx.author, r[raffle])
        except DeniedUserEntryError as e:
            return await ctx.send(str(e))

        async with self.config.guild(ctx.guild).raffles() as r:
            raffle_entities = lambda x: r[raffle].get(x, None)
            raffle_entities("entries").append(ctx.author.id)

        welcome_msg = _("{} you have been added to the raffle.".format(ctx.author.mention))

        join = raffle_entities("join_message")
        if join:
            if isinstance(join, list):
                join = random.choice(join)
            join_message = join.format(
                user=RaffleSafeMember(ctx.author, "user"),
                raffle=raffle,
                entry_count=len(raffle_entities("entries")),
            )
            welcome_msg += "\n---\n{}".format(join_message)

        await ctx.send(welcome_msg)
        await self.clean_guild_raffles(ctx)

    @raffle.command()
    async def leave(self, ctx: Context, raffle: RaffleExists):
        """Leave a raffle.

        **Arguments:**
            - `<raffle>` - The name of the raffle to leave.
        """
        async with self.config.guild(ctx.guild).raffles() as r:

            raffle_data = r.get(raffle, None)
            raffle_entries = raffle_data.get("entries")

            if not ctx.author.id in raffle_entries:
                return await ctx.send(_("You are not entered into this raffle."))

            raffle_entries.remove(ctx.author.id)
            await ctx.send(
                _("{0.mention} you have been removed from the raffle.".format(ctx.author))
            )

        await self.clean_guild_raffles(ctx)

    @raffle.command()
    async def mention(self, ctx: Context, raffle: RaffleFactoryConverter):
        """Mention all the users entered into a raffle.

        **Arguments:**
            - `<raffle>` - The name of the raffle to mention all the members in.
        """
        async with self.config.guild(ctx.guild).raffles() as r:

            raffle_data = r.get(raffle, None)

            raffle_entities = lambda x: raffle_data.get(x)

            if not raffle_entities("entries"):
                return await ctx.send(_("There are no entries yet for this raffle."))

            for page in pagify(
                humanize_list([self.bot.get_user(u).mention for u in raffle_entities("entries")])
            ):
                await ctx.send(page)

        await self.clean_guild_raffles(ctx)

    @raffle.command()
    async def end(self, ctx: Context, raffle: RaffleFactoryConverter):
        """End a raffle.

        **Arguments:**
            - `<raffle>` - The name of the raffle to end.
        """
        async with self.config.guild(ctx.guild).raffles() as r:

            msg = await ctx.send(_("Ending the `{raffle}` raffle...".format(raffle=raffle)))

            r.pop(raffle)

        await asyncio.sleep(1)
        with contextlib.suppress(discord.NotFound):
            await msg.edit(content=_("Raffle ended."))

        await self.clean_guild_raffles(ctx)
