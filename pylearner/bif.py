import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, humanize_list
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .abc import MixinMeta
from .converters import FunctionDescriptorConverter, StatusConverter
from .utils import KEY, mapping, pybox, yield_chunks


class BuiltinFunctions(MixinMeta):
    """Builtin functions mixin"""

    async def sign_bif_markas(self, ctx, status: str, *functions):
        async with self.config.user(ctx.author).functions() as funcs:
            for func in functions:
                if not func in funcs.keys():
                    await ctx.send(pybox(f'"{func}" is not a recognized function.'))
                    return
                if funcs[func]["status"] == status:
                    await ctx.send(pybox(f"This function already has the status {status}."))
                funcs[func]["status"] = status
        await ctx.send(pybox(f"{humanize_list(functions)} successfully marked as {status}."))

    @commands.group()
    async def bif(self, ctx):
        """Commands with builtin functions."""
        pass

    @bif.command(name="list")
    async def bif_list(self, ctx, status: StatusConverter = None):
        """Get your revision map for builtin functions."""
        funcs = await self.config.user(ctx.author).functions()

        embeds_list = []

        if status is not None:
            _dict = {k: v for k, v in funcs.items() if v["status"] == status}
            items = _dict.items()
            defined_status = True
        else:
            items = funcs.items()
            defined_status = False

        if not items:
            return await ctx.send("There are no functions.")

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
                return await ctx.send("There are no functions.")
            description += box(f"Page {page}/{len(chunks)}", "fix")

            embed = discord.Embed(
                title="Python Functions Learning List",
                description=description,
                color=await ctx.embed_colour(),
            )
            embed.set_footer(text=f"Page {page}/{len(chunks)}")

            if not defined_status:
                embed.add_field(
                    name="Key",
                    value=box(KEY, "prolog"),
                )

            embeds_list.append(embed)
        await menu(ctx, embeds_list, DEFAULT_CONTROLS)

    @bif.command(name="load")
    async def bif_load(self, ctx, *functions):
        """Load functions to appear in the functions list."""
        async with self.config.user(ctx.author).functions() as funcs:
            for function in functions:
                if not function in funcs.keys():
                    await ctx.send(pybox(f'"{function}" is not a recognized function.'))
                    return
                if funcs[function]["loaded"] is True:
                    await ctx.send(pybox(f"{function} is already loaded."))
                    return
                funcs[function]["loaded"] = True
        if functions:
            await ctx.send(pybox(f"{humanize_list(functions)} successfully loaded."))
        else:
            await ctx.send_help()

    @bif.command(name="loadstate")
    async def bif_loadstate(self, ctx):
        """Shows the loaded and unloaded functions."""
        functions = await self.config.user(ctx.author).functions()
        loaded = list(filter(lambda x: x[1]["loaded"], list(functions.items())))
        unloaded = list(filter(lambda x: not x[1]["loaded"], list(functions.items())))
        print(loaded, unloaded)
        message = f"Loaded functions ({len(loaded)}):\n" + ", ".join([i[0] for i in loaded])
        message += f"\n\nUnloaded functions ({len(unloaded)}):\n" + ", ".join(
            [i[0] for i in unloaded]
        )
        await ctx.send(pybox(message))

    @bif.command(name="unload")
    async def bif_unload(self, ctx, *functions):
        """Unload functions to disappear from the functions list."""
        async with self.config.user(ctx.author).functions() as funcs:
            for function in functions:
                if not function in funcs.keys():
                    await ctx.send(pybox(f'"{function}" was not a recognized function.'))
                    return
                if funcs[function]["loaded"] is False:
                    await ctx.send(pybox(f'"{function}" is already unloaded.'))
                    return
                funcs[function]["loaded"] = False
        if functions:
            await ctx.send(pybox(f"{humanize_list(functions)} successfully unloaded."))
        else:
            await ctx.send_help()

    @bif.group(name="markas")
    async def bif_markas(self, ctx):
        """Mark builtin functions with statuses."""

    @bif_markas.command(name="complete")
    async def bif_markas_complete(self, ctx, *functions):
        """Mark a function as complete."""
        await self.sign_bif_markas(ctx, "complete", *functions)

    @bif_markas.command(name="incomplete")
    async def bif_markas_incomplete(self, ctx, *functions):
        """Mark a function as incomplete."""
        await self.sign_bif_markas(ctx, "incomplete", *functions)

    @bif_markas.command(name="partial")
    async def bif_markas_partial(self, ctx, *functions):
        """Mark a function as partial."""
        await self.sign_bif_markas(ctx, "partial", *functions)

    @bif_markas.command(name="interested")
    async def bif_markas_interested(self, ctx, *functions):
        """Mark a function as interested."""
        await self.sign_bif_markas(ctx, "interested", *functions)

    @bif.command(name="doc")
    async def bif_doc(self, ctx, function: FunctionDescriptorConverter):
        """Get the doc for a function."""
        # Converters <3
        await ctx.send(function)
