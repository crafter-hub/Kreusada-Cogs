import builtins
import json
import keyword
import pathlib
import types

from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import humanize_list

from .abc import MetaClass
from .bif import BuiltinFunctions
from .kwd import Keywords

with open(pathlib.Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


filtered_builtins = filter(
    lambda x: isinstance(x, types.BuiltinFunctionType), map(eval, dir(builtins))
)


class PyLearner(BuiltinFunctions, Keywords, commands.Cog, metaclass=MetaClass):
    """A cog used with tracking my progress in python!"""

    __author__ = ["Kreusada"]
    __version__ = "1.0.0"

    user_config = {
        "keywords": {kw: {"status": "incomplete", "loaded": True} for kw in keyword.kwlist},
        "functions": {
            func: {"status": "incomplete", "loaded": func not in ("__import__", "__build_class__")}
            for func in map(lambda x: x.__name__, filtered_builtins)
        },
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 5234894734289056, True)
        self.config.register_user(**self.user_config)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        context = super().format_help_for_context(ctx)
        authors = humanize_list(self.__author__)
        return "{context}\n\nAuthor: {authors}\nVersion: {version}".format(
            context=context, authors=authors, version=self.__version__
        )

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return
