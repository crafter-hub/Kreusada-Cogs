from typing import Literal

import discord
from redbot.core.commands import Context
from redbot.core.i18n import Translator

from .checks import VALID_USER_BADGES, account_age_checker, now, server_join_age_checker
from .enums import RaffleComponents
from .exceptions import (
    DeniedUserEntryError,
    InvalidArgument,
    InvalidConditionCrossover,
    RaffleDeprecationWarning,
    RaffleSyntaxError,
    RequiredKeyError,
    UnidentifiedKeyError,
    UnknownEntityError,
)
from .helpers import format_underscored_text, has_badge, raffle_safe_member_scanner

__all__ = ("RaffleManager",)
_ = Translator("Raffle", __file__)


class RaffleManager(object):
    """Parses the required and relevant yaml data to ensure
    that it matches the specified requirements."""

    def __init__(self, data, raffle_type: Literal["command", "reaction"]):
        super().__init__()
        self.data = data
        self.name = data.get("name", None)
        self.description = data.get("description", None)
        self.account_age = data.get("account_age", None)
        self.server_join_age = data.get("server_join_age", None)
        self.maximum_entries = data.get("maximum_entries", None)
        self.roles_needed_to_enter = data.get("roles_needed_to_enter", None)
        self.badges_needed_to_enter = data.get("badges_needed_to_enter", None)
        self.prevented_users = data.get("prevented_users", None)
        self.allowed_users = data.get("allowed_users", None)
        self.join_message = data.get("join_message", None)
        self.end_message = data.get("end_message", None)
        self.on_end_action = data.get("on_end_action", None)
        self.suspense_timer = data.get("suspense_timer", None)
        self.reaction_emoji = data.get("reaction_emoji", None)

        self.raffle_type = raffle_type

        # dep warnings come first
        if "join_age" in self.data.keys():
            raise RaffleDeprecationWarning(
                '"join_age" has been deprecated in favour of "server_join_age". Please use this condition instead.'
            )

        # now if something isn't recognised
        for key in self.data.keys():
            if not key in [x.name for x in RaffleComponents]:
                raise UnidentifiedKeyError(f'"{key}" is not a documented condition/block')

        # these keys won't actually be parsed if the type is wrong, but its best to raise here anyway
        if raffle_type != "reaction":
            if self.reaction_emoji:
                raise InvalidConditionCrossover(
                    f"(reaction_emoji) this condition cannot be used with the {raffle_type} raffle type"
                )

    @classmethod
    def shorten_description(cls, description, length=50):
        if len(description) > length:
            return description[:length].rstrip() + "..."
        return description

    @classmethod
    def parse_accage(cls, accage: int):
        if not account_age_checker(accage):
            raise InvalidArgument("Days must be less than Discord's creation date")

    @classmethod
    def parse_serverjoinage(cls, ctx: Context, new_join_age: int):
        guildage = (now - ctx.guild.created_at).days
        if not server_join_age_checker(ctx.guild, new_join_age):
            raise InvalidArgument(
                "Days must be less than this guild's creation date ({} days)".format(guildage)
            )

    def parser(self, ctx: Context):
        if self.account_age:
            if not isinstance(self.account_age, int):
                raise RaffleSyntaxError("(account_age) days must be a number")
            if not account_age_checker(self.account_age):
                raise RaffleSyntaxError(
                    "(account_age) days must be less than Discord's creation date"
                )

        if self.server_join_age:
            if not isinstance(self.server_join_age, int):
                raise RaffleSyntaxError("(server_join_age) days must be a number")
            if not server_join_age_checker(ctx.guild, self.server_join_age):
                raise RaffleSyntaxError(
                    "(server_join_age) days must be less than this servers's creation date"
                )

        if self.maximum_entries:
            if not isinstance(self.maximum_entries, int):
                raise RaffleSyntaxError("(maximum_entries) Maximum entries must be a number")

        if self.name:
            if not isinstance(self.name, str):
                raise RaffleSyntaxError("(name) Name must be in quotation marks")
            if len(self.name) > 25:
                raise RaffleSyntaxError(
                    "(name) Name must be under 25 characters, your raffle name had {}".format(
                        len(self.name)
                    )
                )
            for char in self.name:
                if char == "_":
                    # We want to allow underscores
                    continue
                if not char.isalnum():
                    index = self.name.index(char)
                    marker = (
                        f"{self.name}\n{' ' * (index)}^\n"
                        f'Characters must be alphanumeric or underscores, not "{char}"'
                    )
                    raise RaffleSyntaxError(f'In "name" field, character {index+1}\n\n{marker}')
        else:
            raise RequiredKeyError("name")

        if self.description:
            if not isinstance(self.description, str):
                raise RaffleSyntaxError("(description) Description must be in quotation marks")

        if self.roles_needed_to_enter:
            if not isinstance(self.roles_needed_to_enter, list):
                raise RaffleSyntaxError(
                    "(roles_needed_to_enter) Roles must be a list of Discord role IDs"
                )
            for r in self.roles_needed_to_enter:
                if not isinstance(r, int):
                    raise RaffleSyntaxError(
                        f'(roles_needed_to_enter) "{r}" must be a number (role ID) without quotation marks'
                    )
                if not ctx.guild.get_role(r):
                    raise UnknownEntityError(r, "role")

        if self.badges_needed_to_enter:
            if not isinstance(self.badges_needed_to_enter, list):
                raise RaffleSyntaxError(
                    "(badges_needed_to_enter) Badges must be a list of Discord badge names"
                )
            for b in self.badges_needed_to_enter:
                if not isinstance(b, str):
                    raise RaffleSyntaxError(
                        f'(badges_needed_to_enter) "{b}" must be a Discord badge wrapped in quotation marks'
                    )
                if not b in VALID_USER_BADGES:
                    raise InvalidArgument(
                        f'(badges_needed_to_enter) "{b}" is not a recognized Discord badge'
                    )

        if self.prevented_users:
            if not isinstance(self.prevented_users, list):
                raise RaffleSyntaxError(
                    "(prevented_users) Prevented users must be a list of Discord user IDs"
                )
            for u in self.prevented_users:
                if not isinstance(u, int):
                    raise RaffleSyntaxError(
                        f'"{u}" must be a number (user ID) without quotation marks'
                    )
                if not ctx.bot.get_user(u):
                    raise UnknownEntityError(u, "user")

        if self.allowed_users:
            if not isinstance(self.allowed_users, list):
                raise RaffleSyntaxError(
                    "(allowed_users) Allowed users must be a list of Discord user IDs"
                )
            for u in self.allowed_users:
                if not isinstance(u, int):
                    raise RaffleSyntaxError(
                        f'"{u}" must be a number (user ID) without quotation marks'
                    )
                if not ctx.bot.get_user(u):
                    raise UnknownEntityError(u, "user")

        if self.end_message:
            if not isinstance(self.end_message, (list, str)):
                raise RaffleSyntaxError(
                    "(end_message) End message must be in quotation marks, by itself or inside a list"
                )
            if isinstance(self.end_message, str):
                raffle_safe_member_scanner(self.end_message, "end_message")
            else:
                for m in self.end_message:
                    if not isinstance(m, str):
                        raise RaffleSyntaxError(
                            "All end messages must be wrapped by quotation marks"
                        )
                    raffle_safe_member_scanner(m, "end_message")

        if self.join_message:
            if not isinstance(self.join_message, (list, str)):
                raise RaffleSyntaxError(
                    "(join_message) Join message must be in quotation marks, by itself or inside a list"
                )
            if isinstance(self.join_message, str):
                raffle_safe_member_scanner(self.join_message, "join_message")
            else:
                for m in self.join_message:
                    if not isinstance(m, str):
                        raise RaffleSyntaxError(
                            "All join messages must be wrapped by quotation marks"
                        )
                    raffle_safe_member_scanner(m, "join_message")

        if self.on_end_action:
            valid_actions = ("end", "remove_winner", "remove_and_prevent_winner", "keep_winner")
            if not isinstance(self.on_end_action, str) or self.on_end_action not in valid_actions:
                raise InvalidArgument(
                    "(on_end_action) must be one of 'end', 'remove_winner', 'remove_and_prevent_winner', or 'keep_winner'"
                )

        if self.suspense_timer:
            if not isinstance(self.suspense_timer, int) or self.suspense_timer not in [
                *range(0, 11)
            ]:
                raise InvalidArgument("(suspense_timer) must be a number between 0 and 10")

        if self.reaction_emoji:
            if not isinstance(self.reaction_emoji, str):
                raise RaffleSyntaxError(
                    "(reaction_emoji) Reaction emoji must be an emoji-string inside quotation marks, or an emoji"
                )

    @classmethod
    def check_user_entry(cls, user: discord.Member, data: dict):
        raffle_entities = lambda x: data.get(x, None)

        guild = user.guild

        if user.id in raffle_entities("entries"):
            raise DeniedUserEntryError(_("You are already in this raffle."))

        if raffle_entities("prevented_users") and user.id in raffle_entities("prevented_users"):
            raise DeniedUserEntryError(_("You are not allowed to join this particular raffle."))

        if raffle_entities("allowed_users") and user.id not in raffle_entities("allowed_users"):
            raise DeniedUserEntryError(_("You are not allowed to join this particular raffle"))

        if user.id == raffle_entities("owner"):
            raise DeniedUserEntryError(_("You cannot join your own raffle."))

        if raffle_entities("maximum_entries") and len(
            raffle_entities("entries")
        ) > raffle_entities("maximum_entries"):
            raise DeniedUserEntryError(
                _("Sorry, the maximum number of users have entered this raffle.")
            )

        if raffle_entities("roles_needed_to_enter"):
            for r in raffle_entities("roles_needed_to_enter"):
                if not r in [x.id for x in user.roles]:
                    raise DeniedUserEntryError(
                        _("You are missing a required role: {}".format(guild.get_role(r).mention))
                    )

        if raffle_entities("account_age") and not account_age_checker(
            raffle_entities("account_age")
        ):
            raise DeniedUserEntryError(
                _(
                    "Your account must be at least {} days old to join.".format(
                        raffle_entities("account_age")
                    )
                )
            )

        if raffle_entities("server_join_age") and not server_join_age_checker(
            guild, raffle_entities("server_join_age")
        ):
            raise DeniedUserEntryError(
                _(
                    "You must have been in this guild for at least {} days to join.".format(
                        raffle_entities("server_join_age")
                    )
                )
            )

        if raffle_entities("badges_needed_to_enter"):
            for badge in raffle_entities("badges_needed_to_enter"):
                if not has_badge(badge, user):
                    raise DeniedUserEntryError(
                        _(
                            'You must have the "{}" Discord badge to join.'.format(
                                format_underscored_text(badge)
                            )
                        )
                    )
