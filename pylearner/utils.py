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

KEY = f"""[{mapping["complete"]}] Completed
[{mapping["partial"]}] Partial Progress
[{mapping["interested"]}] Interested
[{mapping["incomplete"]}] Incomplete
"""
