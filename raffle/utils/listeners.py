import contextlib

import discord
from redbot.core import commands

from .exceptions import DeniedUserEntryError
from ..mixins.abc import RaffleMixin
from ..mixins.metaclass import MetaClass
from .parser import RaffleManager


class Listeners(RaffleMixin, metaclass=MetaClass):
    """Listeners for Raffle (probably for reaction raffles)"""

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):

        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if not guild:
            return

        if user.bot:
            return

        if await self.bot.cog_disabled_in_guild(self, guild):
            return

        if not await self.bot.ignored_channel_or_guild(message):
            return

        if not await self.bot.allowed_by_whitelist_blacklist(user):
            return

        raffle_config = await self.config.guild(guild).raffles()

        for raffle in raffle_config.keys():
            if raffle_config[raffle]["external-settings"]["type"] != "reaction":
                continue
            if raffle_config[raffle]["reaction_emoji"] != str(payload.emoji):
                continue
            if raffle_config[raffle]["external-settings"]["msgid"] != payload.message_id:
                continue

            kwargs = {}

            try:
                RaffleManager.check_user_entry(user, raffle_config[raffle])
            except DeniedUserEntryError as e:
                kwargs["content"] = str(e).lower()
                await message.remove_reaction(raffle_config[raffle]["reaction_emoji"], user)
            else:
                kwargs["content"] = "You have been entered into the raffle!"
                raffle_config[raffle]["entries"].append(user.id)
                await self.config.guild(guild).raffles.set(raffle_config)
            finally:
                try:
                    await user.send(**kwargs)
                except discord.HTTPException:
                    kwargs["delete_after"] = 2.5
                    kwargs["content"] = f"{user.mention} " + kwargs["content"]
                    await channel.send(**kwargs)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if not guild:
            return

        if user.bot:
            return

        if await self.bot.cog_disabled_in_guild(self, guild):
            return

        if not await self.bot.ignored_channel_or_guild(message):
            return

        if not await self.bot.allowed_by_whitelist_blacklist(user):
            return

        raffle_config = await self.config.guild(guild).raffles()

        for raffle in raffle_config.keys():
            if raffle_config[raffle]["external-settings"]["type"] != "reaction":
                continue
            if raffle_config[raffle]["reaction_emoji"] != str(payload.emoji):
                continue
            if raffle_config[raffle]["external-settings"]["msgid"] != payload.message_id:
                continue

            with contextlib.suppress(ValueError):
                raffle_config[raffle]["entries"].remove(payload.user_id)
                await self.config.guild(guild).raffles.set(raffle_config)
                return