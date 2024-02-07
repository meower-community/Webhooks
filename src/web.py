import os

import MeowerBot.api
import sanic.exceptions
from pymongo import MongoClient
from sanic import Blueprint, Request, Sanic, json
from typing import TYPE_CHECKING
from database import Database, Webhook
from os import environ as env
from dotenv import load_dotenv

load_dotenv()

from better_profanity import profanity


app = Sanic("Webhooks")
api = MeowerBot.api.MeowerAPI("Webhooks")
database = Database(env.get("DB_URL", "mongodb://localhost:27017"), env.get("DB_NAME", "webhooks"))

@app.post("/internal/token")
async def internal_token(request: Request):
    # check if reverse proxy
    if request.headers.get("CF-Connecting-IP") is not None:
        raise sanic.exceptions.NotFound

    await api.login(request.body)
    return sanic.empty()


@app.post("/webhook/<id:str>/<token:str>/<chat_id>/post")
async def send(request: Request, id, token, chat_id):
    data = request.json
    if 'name' not in data:
        raise sanic.exceptions.BadRequest(message="name")

    if 'message' not in data:
        raise sanic.exceptions.BadRequest(message="message")

    webhook = database.get_webhook(id, token, str(chat_id))
    if type(webhook) is tuple:
        return json({"error": True, "message": webhook[0]}, webhook[1])

    if profanity.contains_profanity(data["message"]):
        return json({"error": True, "message": "Message contains profanity."}, 400)

    resp, status = await api.send_post(str(chat_id), f"{webhook['_id']}: {data["name"]}: {data['message']}")
    if status != 200:
        return json(resp, status)  # forward it

    return json(resp.to_dict())


def _raw_get_webhook(id, database) -> Webhook | None:
    return database.con.webhooks.find_one({"_id": id})


@app.get("/profile/<id>/")
async def get_profile(request: Request, id):

    webhook = _raw_get_webhook(id, database)

    if webhook is None:
        return json({"error": True, "message": "Webhook not found"}, 404)



    return json({
        "error": False,
        "pfp": webhook.get("profile_picture"),
        "chat_id": webhook.get("chat_id"),
        "perms": webhook.get("perms")
    })

@app.exception(sanic.exceptions.NotFound)
async def not_found(_: Request, resp: sanic.HTTPResponse):
    raise sanic.exceptions.NotFound()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=10000, dev=True, debug=True)