from MeowerBot import Bot
from MeowerBot.cog import Cog
from MeowerBot.command import command
from MeowerBot.context import Context, Post
from MeowerBot.data.api.user import Permissions, Relationship
from sanic import Sanic
import database

def has_permission(user_permissions, permission):
    if ((user_permissions & Permissions.SYSADMIN) == Permissions.SYSADMIN):
        return True
    else:
        return ((user_permissions & permission) == permission)

owner = "ShowierData9978"


def requires_permission(permission):
    def decorator(func):
        async def wrapper(self, ctx, *args, **kwargs):
            if not has_permission(ctx.user.permissions, permission) and ctx.user.name != owner:
                await ctx.send_msg("You do not have permission to use this command.")
                return
            return await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator


class Moderation(Cog):
    def __init__(self, bot: "Webhooks"):
        super().__init__()
        self.bot = bot

    @command()
    async def mod(self, ctx: Context):
        """
            Mod command base

            do not call directly, use one of the subcommands
        """
        await ctx.send_msg("@WebhookMod mod is not meant to be called directly.")

    @mod.subcommand("ban", 1)
    @requires_permission(Permissions.EDIT_BAN_STATES)
    async def ban(self, ctx: Context, user: str):
        """
            Ban a user.

            Parameters:
                user (str): The username of the user to ban.

            Permissions:
                EDIT_BAN_STATES
        """

        self.bot.db.ban_user(user, True)
        await ctx.send_msg(f"Banned {user}.")




class Webhooks(Bot):
    def __init__(self, prefix=None, app: Sanic = None):
        super().__init__(prefix)


        if app is None:
            raise TypeError("app is required")

        assert app.ctx.db is not None and isinstance(app.ctx.db, database.Database)
        self.db: database.Database = app.ctx.db

        if app.ctx.bot is None:
            app.ctx.bot = self

        self.moderation = Moderation(self)
        self.register_cog(self.moderation)

    async def message(self, message: Post):
        message = await self.handle_bridges(message)

        if self.db.get_user(message.user.username).get("banned"):
            return await (
                self.get_chat(
                    await self.api.users.dm(message.user.username)
                )
            ).send_msg("You are banned from webhooks.")

        if not message.data.startswith(self.prefix):
            return

        message.data = message.data.removeprefix(self.prefix)

        await self.run_commands(message)
