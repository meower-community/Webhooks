from MeowerBot import Bot
from MeowerBot.cog import Cog
from MeowerBot.command import command
from MeowerBot.context import Context, Post, Chat
from MeowerBot.data.api.user import Permissions
import database


# noinspection PyRedundantParentheses
def has_permission(user_permissions, permission):
    if ((user_permissions & Permissions.SYSADMIN) == Permissions.SYSADMIN):
        return True
    else:
        return ((user_permissions & permission) == permission)

owner = "ShowierData9978"


def requires_permission(permission):
    def decorator(func):
        async def wrapper(self, ctx: Context, *args, **kwargs):
            ctx.user = await ctx.user.fetch()
            if not has_permission(ctx.user.permissions, permission) and ctx.user.name != owner:
                await ctx.send_msg("You do not have permission to use this command.")
                return
            return await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator


# noinspection PyIncorrectDocstring
class Moderation(Cog):
    def __init__(self, bot: "Webhooks"):
        super().__init__()
        self.bot = bot

    @command()
    async def mod(self, ctx: Context):
        """
            Mod command base

            Do not call directly, use one of the subcommands
        """
        await ctx.send_msg("@Webhooks mod is not meant to be called directly.")

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
        
    @mod.subcommand("delete_webhook", args=1)
    @requires_permission(Permissions.EDIT_BAN_STATES)
    async def delete_webhook(self, ctx: Context, webhook_id: int):
        webhook_id = int(webhook_id)
        self.bot.db.delete_webhook(webhook_id)


    @mod.subcommand("create", 2)
    @requires_permission(0) # No permissions required
    async def create(self, ctx: Context, chat: str, pfp: int):
        """
            Create a webhook.
        """

        # try to get the chat

        if chat in ["home", "livechat"]:
            await ctx.send_msg("Unreachable.")
            return

        if (full_chat := await self.bot.get_chat(chat).fetch()) is None:
            await ctx.send_msg(f"Please invite {self.bot.username} to {chat}.")
            return

        if (full_chat.owner != ctx.user.username) and (full_chat.owner is not None):
            await ctx.send_msg("You are not the owner of this chat.")
            return

        token, id = self.bot.db.create_webhook(pfp, chat) # type: str
        user_dm = Chat((await self.bot.api.users.dm(ctx.user.username))[0], self.bot)

        await ctx.reply("I have sent your webhook via DM's")
        await user_dm.send_msg(f"Your webhook: https://webhooks.meower.org/webhook/{id}/{token}/{chat}/post")

    @create.subcommand("home", 1)
    @requires_permission(Permissions.EDIT_CHATS)
    async def create_home(self, ctx: Context, pfp: int):
        token, id = self.bot.db.create_webhook(pfp, "home") # type: str
        user_dm = Chat(await self.bot.api.users.dm(ctx.user.username), self.bot)
        await ctx.reply("I have sent your webhook via DM's")
        await user_dm.send_msg(f"Your webhook: https://webhooks.meower.org/webhook/{id}/{token}/home/post")

    @create.subcommand("livechat", 1)
    @requires_permission(Permissions.EDIT_CHATS)
    async def create_livechat(self, ctx: Context, pfp: int):
        token, id = self.bot.db.create_webhook(pfp, "livechat") # type: str
        user_dm = Chat((await self.bot.api.users.dm(ctx.user.username))[0], self.bot)

        await ctx.reply("I have sent your webhook via DM's")
        await user_dm.send_msg(f"Your webhook: https://webhooks.meower.org/webhook/{id}/{token}/livechat/post")




class Webhooks(Bot):
    def __init__(self, prefix=None):
        super().__init__(prefix)

        self.db = None
        self.moderation = Moderation(self)
        self.register_cog(self.moderation)

    def add_app(self, database: database.Database):
        self.db = database

    async def message(self, message: Post):
        message = await self.handle_bridges(message)

        if self.db.get_user(message.user.username).get("banned"):
            return Chat(await self.api.users.dm(message.user.username)[0], self).send_msg("You are banned from webhooks.")

        if not message.data.startswith(self.prefix):
            return

        message.data = message.data.removeprefix(self.prefix)

        await self.run_commands(message)
