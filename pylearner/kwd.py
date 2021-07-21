import keyword

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, humanize_list
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .abc import MixinMeta
from .converters import StatusConverter
from .utils import KEY, compose_menu, mapping, pybox, yield_chunks


class Keywords(MixinMeta):
    """Keywords mixin"""

    async def sign_kwd_markas(self, ctx, status: str, *kwds):
        async with self.config.user(ctx.author).keywords() as kw:
            for kwd in kwds:
                if not kwd in kw.keys():
                    await ctx.send(pybox(f'"{kwd}" is not a recognized keyword.'))
                    return
                if kw[kwd]["status"] == status:
                    await ctx.send(pybox(f'"{kwd}" already has the status {status}.'))
                kw[kwd]["status"] = status
        await ctx.send(pybox(f"{humanize_list(kwds)} successfully marked as {status}."))

    @commands.group()
    async def kwd(self, ctx):
        """Commands with python keywords."""
        pass

    @kwd.command(name="list")
    async def kwd_list(self, ctx, status: StatusConverter = None):
        """Get your revision map for keywords."""
        funcs = await self.config.user(ctx.author).keywords()

        embeds_list = []

        if status is not None:
            _dict = {k: v for k, v in funcs.items() if v["status"] == status}
            items = _dict.items()
            defined_status = True
        else:
            items = funcs.items()
            defined_status = False

        if not items:
            return await ctx.send("There are no keywords.")

        if len(items) > 20:
            splitter = len(items) // 4
        else:
            splitter = len(items)
        chunks = list(yield_chunks(list(items), splitter))
        for a in chunks:
            page = len(embeds_list) + 1
            data = []
            for i in a:
                if not i[1]["loaded"]:
                    continue
                data.append((mapping[i[1]["status"]], i[0]))

            if data:
                description = pybox("\n".join(f"[{i[0]}] {i[1]}" for i in data))
            else:
                return await ctx.send("There are no keywords.")
            description += box(f"Page {page}/{len(chunks)}", "fix")

            embed = discord.Embed(
                title="Python Keywords Learning List",
                description=description,
                color=await ctx.embed_colour(),
            )

            if not defined_status:
                embed.add_field(
                    name="Key",
                    value=box(KEY, "prolog"),
                )

            embeds_list.append(embed)
        await compose_menu(ctx, embeds_list)

    @kwd.command(name="load")
    async def kwd_load(self, ctx, *kwds):
        """Load keywords to appear in the keywords list."""
        async with self.config.user(ctx.author).keywords() as kw:
            for kwd in kwds:
                if not kwd in kw.keys():
                    await ctx.send(pybox(f'"{kwd}" is not a recognized keyword.'))
                    return
                if kw[kwd]["loaded"] is True:
                    await ctx.send(pybox(f"{kwd} is already loaded."))
                    return
                kw[kwd]["loaded"] = True
        if kwds:
            await ctx.send(pybox(f"{humanize_list(kwds)} successfully loaded."))
        else:
            await ctx.send_help()

    @kwd.command(name="loadstate")
    async def kwd_loadstate(self, ctx):
        """Shows the loaded and unloaded keywords."""
        keywords = await self.config.user(ctx.author).keywords()
        loaded = list(filter(lambda x: x[1]["loaded"], list(keywords.items())))
        unloaded = list(filter(lambda x: not x[1]["loaded"], list(keywords.items())))
        print(loaded, unloaded)
        message = f"Loaded keywords ({len(loaded)}):\n" + ", ".join([i[0] for i in loaded])
        message += f"\n\nUnloaded keywords ({len(unloaded)}):\n" + ", ".join(
            [i[0] for i in unloaded]
        )
        await ctx.send(pybox(message))

    @kwd.command(name="unload")
    async def kwd_unload(self, ctx, *kwds):
        """Unload keywords to disappear from the keywords list."""
        async with self.config.user(ctx.author).keywords() as kw:
            for kwd in kwds:
                if not kwd in kw.keys():
                    await ctx.send(pybox(f'"{kwd}" was not a recognized keyword.'))
                    return
                if kw[kwd]["loaded"] is False:
                    await ctx.send(pybox(f'"{kwd}" is already unloaded.'))
                    return
                kw[kwd]["loaded"] = False
        if kwds:
            await ctx.send(pybox(f"{humanize_list(kwds)} successfully unloaded."))
        else:
            await ctx.send_help()

    @kwd.group(name="markas")
    async def kwd_markas(self, ctx):
        """Mark keywords with statuses."""

    @kwd_markas.command(name="complete")
    async def kwd_markas_complete(self, ctx, *keywords):
        """Mark a keyword as complete."""
        await self.sign_kwd_markas(ctx, "complete", *keywords)

    @kwd_markas.command(name="incomplete")
    async def kwd_markas_incomplete(self, ctx, *keywords):
        """Mark a keyword as incomplete."""
        await self.sign_kwd_markas(ctx, "incomplete", *keywords)

    @kwd_markas.command(name="partial")
    async def kwd_markas_partial(self, ctx, *keywords):
        """Mark a keyword as partial."""
        await self.sign_kwd_markas(ctx, "partial", *keywords)

    @kwd_markas.command(name="interested")
    async def kwd_markas_interested(self, ctx, *keywords):
        """Mark a keyword as interested."""
        await self.sign_kwd_markas(ctx, "interested", *keywords)
