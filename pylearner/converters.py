import builtins
import inspect
import keyword

from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_list

from .utils import pybox, specific_builtin_functions


class StatusConverter(commands.Converter):
    args = ("complete", "incomplete", "partial", "interested")

    async def convert(self, ctx: commands.Context, status):
        if not status in self.args:
            raise commands.BadArgument(
                "Status must be one of %s." % humanize_list(self.args, style="or")
            )
        return status


class KWDConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, kwd):
        if not kwd in keyword.kwlist:
            raise commands.BadArgument("%s is not a python keyword" % kwd)
        return kwd


class FunctionDescriptorConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, function):
        if not function in specific_builtin_functions:
            raise commands.BadArgument('"%s" is not a valid builtin function.' % function)
        return pybox(inspect.getdoc(getattr(builtins, function)))
