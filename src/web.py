from sanic import Blueprint, Request, json
from MeowerBot import Bot
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bot import Webhooks

webhook_bp = Blueprint()
bot: Webhooks = None


def loaded(_bot):
    global bot
    bot = _bot


@webhook_bp.post("/<id>/<token>/")
async def send(request: Request, chat_id, token):
    if not isinstance(request.app.bot, Bot):
        return json({"error": True, "message": "Failed to get bot."})

    # TODO: Implement Database stuff
    #  I cant do this via ssh on my phone
    data = request.json()
    bot: Bot = request.app.bot
    resp, status = await bot.api.send_msg(f"{data['name']}: {data['message']}", chat_id)
    if status != 200:
        return resp, status  # forward it

    return json(resp.to_dict())
