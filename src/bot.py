from pydoc import text
from typing import Any, Dict

from MeowerBot import Bot
from MeowerBot.cog import Cog
from MeowerBot.command import command
from MeowerBot.context import Context, Post, Chat, User, PartialUser
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

class ModerationService:
    def __init__(self, bot: 'Webhooks'):
        self.bot = bot

    async def ban(self, author: User, user: str):
        if ((author.permissions & Permissions.EDIT_CHATS) != Permissions.EDIT_CHATS) and (author.name != owner):
            return "You do not have permission to use this command.", 403

        # noinspection PyStatementEffect
        self.bot.db.ban_user(user)
        return f"Banned {user}", 200

    async def delete_webhook(self, author: User, webhook_id: str):
        if ((author.permissions & Permissions.EDIT_CHATS) != Permissions.EDIT_CHATS) and (author.name != owner):
            return "You do not have permission to use this command.", 403

        self.bot.db.delete_webhook(webhook_id)

        return f"Deleted {webhook_id}", 200

    async def create_webhook(self, author: User, chat: str, pfp: int):
        if (author.permissions & Permissions.EDIT_CHATS) != Permissions.EDIT_CHATS  \
           and (chat == "home" or chat == "livechat") and (author.name != owner):

            return "You do not have permission to use this command.", 403
        elif (chat == "home" or chat == "livechat"):
            token, id = self.bot.db.create_webhook(pfp, "livechat")  # type: str
            return f"Webhook created", {"token": token, "id": id}, 200


        if (await self.bot.get_chat(chat).fetch()) is None:
            return f"Please invite {self.bot.username} to {chat}", 428

        token, id = self.bot.db.create_webhook(pfp, chat) # type: str
        return f"Webhook created", {"token": token, "id": id}, 200


# noinspection PyIncorrectDocstring,PyTypeChecker
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

        await self.bot.mod_service.ban(ctx.user, user)
        await ctx.send_msg(f"Banned {user}.")
        
    @mod.subcommand("delete_webhook", args=1)
    @requires_permission(Permissions.EDIT_BAN_STATES)
    async def delete_webhook(self, ctx: Context, webhook_id: int):
        webhook_id = int(webhook_id)
        resp = await self.bot.mod_service.delete_webhook(ctx.user, webhook_id)
        match resp[-1]:
            case 403:
                await ctx.reply(resp[0])
            case 200:
                await ctx.reply("deleted webhook")

    @mod.subcommand("create", 2)
    async def create(self, ctx: Context, chat: str, pfp: int):
        """
            Create a webhook.
        """

        # try to get the chat

        resp = await self.bot.mod_service.create_webhook(ctx.user, chat, pfp)
        match resp[-1]:
            case 200:
                user_dm = Chat((await self.bot.api.users.dm(ctx.user.username))[0], self.bot)
                id = resp[1]["id"]
                token = resp[1]["token"]
                await ctx.reply("I have sent your webhook via DM's")
                await user_dm.send_msg(f"0: Your webhook: https://webhooks.meower.org/webhook/{id}/{token}/{chat}/post")
            case 403:
                await ctx.reply(resp[0])
            case 428:
                await ctx.reply(resp[0])

    @command(name="docs")
    async def documentation(self, ctx: Context):
        msg = """0: Webhooks: 
        
        - [API](https://github.com/meower-community/Webhooks/blob/main/docs/api.md)
        - [PMSG](https://github.com/meower-community/Webhooks/blob/main/docs/pmsg.md)
        """

        fixed = ""
        for line in msg.split("\n"):
            fixed += line.replace("    ", "") + "\n"

        await ctx.send_msg(fixed)

class Webhooks(Bot):
    def __init__(self, prefix=None):
        super().__init__(prefix)

        self.db: database = None
        self.moderation = Moderation(self)
        self.mod_service = ModerationService(self)
        self.register_cog(self.moderation)

    def add_app(self, database: database.Database):
        self.db = database

    async def message(self, message: Post):
        message = await self.handle_bridges(message)

        if self.db.get_user(message.user.username).get("banned"):
            return Chat((await self.api.users.dm(message.user.username))[0], self).send_msg("You are banned from webhooks.")

        if not message.data.startswith(self.prefix):
            return

        message.data = message.data.removeprefix(self.prefix)

        await self.run_commands(message)

    async def send_pmsg(self, packet: Dict[str, Any], val):
        await self.sendPacket({
            "cmd": "pmsg",
            "val": {**val,"listener": packet["val"].get("listener")},
            "id": packet.get("origin")
        })

    async def _message(self, packet: dict):
        await (super())._message(packet)
        if packet.get("cmd") != "pmsg":
            return

        if type(packet["val"]) is not dict:
            return

        if packet["val"].get("cmd") is None:
            return

        if self.db.get_user(packet["origin"]).get("banned"):
            return await self.send_pmsg(packet, {
                "status": 403,
                "error": True
            })

        command = packet["val"]["cmd"]
        val = packet["val"]["val"]
        user = await PartialUser(packet["origin"], self).fetch()
        match command:
            case "create":
                resp = await self.mod_service.create_webhook(user, val["chat"], val["pfp"])
                if resp[-1] != 200:
                    resp = {
                        "error": True,
                        "status": resp[-1],
                        "human": resp[0]
                    }
                else:
                    resp = {
                        **resp[1],
                        "chat": val["chat"],
                        "status": 200
                    }

                await self.send_pmsg(packet, resp)

            case "ban":
                resp = await self.mod_service.ban(user, val)
                await self.send_pmsg(packet, {
                    "status": resp[-1],
                    "error": resp[-1] != 200
                })

            case "delete":
                resp = await self.mod_service.delete_webhook(user, val)
                await self.send_pmsg(packet, {
                    "status": resp[-1],
                    "error": resp[-1] != 200
                })



