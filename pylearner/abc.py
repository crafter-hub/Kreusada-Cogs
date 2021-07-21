from abc import ABC

from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.commands import Cog


class MixinMeta(ABC):
    def __init__(self, *nargs):
        self.config: Config
        self.bot: Red


class MetaClass(type(ABC), type(Cog)):
    pass
