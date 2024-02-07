import os
import uuid

from pymongo import MongoClient
from typing import TypedDict
from secrets import token_urlsafe
from typing import Tuple

from bcrypt import hashpw, gensalt, checkpw

PERM_ALLOW_ALL_CHATS = 1


def has_permission(user_permissions, permission):
    if ((user_permissions & PERM_ALLOW_ALL_CHATS) == PERM_ALLOW_ALL_CHATS):
        return True
    else:
        return ((user_permissions & permission) == permission)


def add_permission(user_permissions, permission):
    return user_permissions | permission


class Webhook(TypedDict):
    _id: str
    token: bytes # bcrypt hash
    profile_picture: int
    chat_id: str

    perms: int


class User(TypedDict):
    username: str
    banned: bool


class Database:
    def __init__(self, url, name) -> None:
        self.con = MongoClient(url)[name]

    def get_webhook(self, id, token, chat_id=None) -> Webhook | Tuple[str, int]:
        # raise an error is PERM_ALLOW_ALL_CHATS, if chat_id != Webhook["chat_id"]

        data: Webhook | None = self.con.webhooks.find_one({"_id": id})

        if data is None:
            return "404 Not Found", 404

        data = Webhook(**data)

        if chat_id is not None and data["chat_id"] != chat_id:
            return "Chat id does not match", 400

        if not checkpw(token.encode(), data["token"]):
            return "Invalid token", 401

        return data

    def set_webhook_perms(self, id, perms):
        return self.con.webhooks.update_one({"_id": id}, {"$set": {"perms": perms}}) == 1

    def delete_webhook(self, id):
        return self.con.webhooks.delete_one({"_id": id}) == 1

    def create_webhook(self, profile_picture, chat_id):
        token = token_urlsafe(32)
        id = str(uuid.uuid4())

        req = self.con.webhooks.insert_one(
            Webhook(
                _id=id,
                token=hashpw(token.encode(), gensalt()),
                profile_picture=profile_picture,
                chat_id=chat_id,
                perms=0,
            )
        )

        # annoying workaround
        return token, req.inserted_id

    def get_user(self, username) -> User:
        data: User | None = self.con.users.find_one({"_id": username})

        if data is None:
            # create a new user
            self.con.users.insert_one(User(username=username, banned=False))
            data = User(username=username, banned=False)

        return data

    def ban_user(self, username):
        self.con.users.update_one({"_id": username}, {"$set": {"banned": True}})
