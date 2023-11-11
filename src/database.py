from pymongo import MongoClient
from typing import TypedDict
from secrets import token_urlsafe

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

    def get_webhook(self, id, token, chat_id=None) -> Webhook:
        # raise an error is PERM_ALLOW_ALL_CHATS, if chat_id != Webhook["chat_id"]

        data: Webhook | None = self.con.webhooks.find_one({"_id": id})


        if data is None:
            return None

        data = Webhook(**data)

        if chat_id is not None and data["chat_id"] != chat_id:
            raise ValueError("Chat id does not match")

        if not checkpw(data["token"], token.encode()):
            raise PermissionError("Token does not match")

        return data

    def set_webhook_perms(self, id, perms):
        return self.con.webhooks.update_one({"_id": id}, {"$set": {"perms": perms}}) == 1

    def delete_webhook(self, id):
        return self.con.webhooks.delete_one({"token": id}) == 1

    def create_webhook(self, profile_picture, chat_id):
        token = token_urlsafe(32)
        req = self.con.webhooks.insert_one(
            Webhook(
                token=hashpw(token.encode(), gensalt()),
                profile_picture=profile_picture,
                chat_id=chat_id,
                perms=0,
            )
        )

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
