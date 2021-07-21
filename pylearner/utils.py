from typing import List

import discord
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.menus import DEFAULT_CONTROLS, close_menu, menu

pybox = lambda x: box(x, lang="py")


def yield_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i : i + n]


async def compose_menu(ctx, embed_pages: List[discord.Embed]):
    if len(embed_pages) == 1:
        control = {"\N{CROSS MARK}": close_menu}
    else:
        control = DEFAULT_CONTROLS
    return await menu(ctx, embed_pages, control)


CROSS = "\N{CROSS MARK}"
CHECK = "\N{HEAVY CHECK MARK}\N{VARIATION SELECTOR-16}"

mapping = {
    "complete": CHECK,
    "incomplete": CROSS,
    "partial": "\N{CONSTRUCTION SIGN}",
    "interested": "\N{EYES}",
}

specific_builtin_functions = [
    "__build_class__",
    "__import__",
    "abs",
    "all",
    "any",
    "ascii",
    "bin",
    "bool",
    "breakpoint",
    "bytearray",
    "bytes",
    "callable",
    "chr",
    "classmethod",
    "compile",
    "complex",
    "delattr",
    "dict",
    "dir",
    "divmod",
    "enumerate",
    "eval",
    "exec",
    "filter",
    "float",
    "format",
    "frozenset",
    "getattr",
    "globals",
    "hasattr",
    "hash",
    "help",
    "hex",
    "id",
    "input",
    "int",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "list",
    "locals",
    "map",
    "max",
    "memoryview",
    "min",
    "next",
    "object",
    "oct",
    "open",
    "ord",
    "pow",
    "print",
    "property",
    "range",
    "repr",
    "reversed",
    "round",
    "set",
    "setattr",
    "slice",
    "sorted",
    "staticmethod",
    "str",
    "sum",
    "super",
    "tuple",
    "type",
    "vars",
    "zip",
]

KEY = f"""[{mapping["complete"]}] Completed
[{mapping["partial"]}] Partial Progress
[{mapping["interested"]}] Interested
[{mapping["incomplete"]}] Incomplete
"""
