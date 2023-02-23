import os
#
import shlex
import string
import time
from json import dump, load
from os import environ as env
from sys import exit
from threading import Thread

from better_profanity import profanity
from MeowerBot import Bot, __version__
from MeowerBot.cog import Cog
from MeowerBot.command import command
import web
from web import app
from MeowerBot.context import Post
from dotenv import load_dotenv
import logging
import requests
load_dotenv(override=True)


# so i dont need to deal with systemd being root.
os.chdir(os.path.dirname(__file__))


with open("banned_ips.json") as b_ips:
    BANNED_IPS = load(b_ips)

with open("users.json") as user_doc:
    USERS = load(user_doc)

def get_remote_adress(request):
    if "X-Forwarded-For" in request.headers:
        return request.headers["X-Forwarded-For"].split(",")[-1]
    return request.access_route[-1]

meower = Bot(prefix="@HookMod", autoreload=0) # 1 second reload time, mb.py adds 1 second to this
meower.DISABLE_GUESTS = False # type: ignore

app.meower = meower # type: ignore
app.BANNED_IPS = BANNED_IPS # type: ignore
app.USERS = USERS # type: ignore

logging.getLogger("cloudlink").setLevel(logging.DEBUG)
logging.getLogger("meowerbot").setLevel(logging.DEBUG)


meower.waiting_for_usr_input = {"usr": "", "waiting": False, "banning": ""} # type: ignore
 
SPECIAL_ADMINS = ["ShowierData9978"]

LVL_CASHE = {}

version = __version__.split(".")

# checking for ^2.2.x

if not version[0] == "2":
    exit(1)


def save_db():
    with open("banned_ips.json", "w") as f:
        dump(BANNED_IPS, f)

    with open("users.json", "w") as f:
        dump(USERS, f)
def fetch_user_level(username):
        if username in LVL_CASHE:
            return LVL_CASHE[username]
        else:
            usr = requests.get(f"https://api.meower.org/users/{username}").json()

            if usr.get("error", True):
                LVL_CASHE[username] = 0
                return 0
            
            LVL_CASHE[username] = usr['lvl']
            return usr['lvl']
class Cogs(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

   
            
    @command(args=1)
    def ban(self, ctx, username):
        BANNED_IPS.append(username)
        save_db()
        ctx.reply(f"banned @{username}")

    @command(args=0)
    def help(self, ctx):
        nl = ",\n  " # getting around fstring syntax
        ctx.reply(f"prefix: @HookMod \ncommands:  {nl.join(list(meower.commands.keys()))}")

    @command(args=1)
    def ipban(self, ctx, username):
        if not fetch_user_level(message.user.username) >= 3 and ctx.message.user.username not in SPECIAL_ADMINS:
            ctx.reply("You dont have enough perms to ip ban for this meower")
            return
    
        if not username in web.usernames_and_ips:
            ctx.reply("Cant Find that user in my ip table ):")
            return

        if meower.waiting_for_user_input.get("usr", "") == ctx.message.user.username and waiting_for_user_input['banning'] == username: # type: ignore
            BANNED_IPS.append(web.usernames_and_ips[username]['ip'])
            save_db()
        else:
            ctx.reply("Are you sure you want to do this, if your sure run the command again") 
            meower.waiting_for_user_input = {"usr": ctx.message.user.username, "banning": username} # type: ignore

    @command(args=1)
    def guests( self, ctx, enable):
        meower.DISABLE_GUESTS = not enable in ["enable", "1", "true", "True"]  # type: ignore
        ctx.reply(f"{'Enabled' if meower.DISABLE_GUESTS else 'Disabled'} Guests")

    @command(args=0)
    def clear_lvl_cache(self, ctx):
        LVL_CASHE.clear()
        ctx.reply("Cleared Cache")

def on_message(message: Post , bot=meower):
    # assuming mb.py 2.2.0
    print(f"{message.user.username}: {message.data}")

    if message.user.username == env["username"]:
        return

    
    if not message.data.startswith(meower.prefix): return
    message.data = message.data.strip().split(meower.prefix, 1)[1].strip()

    if not shlex.split(str(message.data))[0] in meower.commands.keys():
        return
    
    if not fetch_user_level(message.user.username) >= 2 and  message.user.username not in SPECIAL_ADMINS:
        message.ctx.reply("You dont have perms to run commands for this meower") 
        return
    
    meower.run_command(message)


meower.callback(on_message, cbid="message")
meower.register_cog(Cogs(meower))

if __name__ == "__main__":
    profanity.load_censor_words()
    t = Thread(target=app.run, kwargs={"host": "0.0.0.0"})
    t.start()

    try:
        meower.run(env['username'], env['password'])
    except:
        pass
    finally:
        os._exit(0)
