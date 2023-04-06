import os
#
import shlex
import string
import time
from pymongo import MongoClient
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


def get_remote_adress(request):
    if "X-Forwarded-For" in request.headers:
        return request.headers["X-Forwarded-For"].split(",")[-1]
    return request.access_route[-1]

meower = Bot(prefix="@HookMod", autoreload=0) # 1 second reload time, mb.py adds 1 second to this
meower.DISABLE_GUESTS = False # type: ignore

app.meower = meower # type: ignore
app.db = MongoClient(env.get("MONGO_URI")).get_database("Webhooks") 
db: MongoClient = app.db




logging.getLogger("cloudlink").setLevel(logging.DEBUG)
logging.getLogger("meowerbot").setLevel(logging.DEBUG)


meower.waiting_for_usr_input = {"usr": "", "waiting": False, "banning": ""} # type: ignore
 
SPECIAL_ADMINS = ["ShowierData9978"]

LVL_CASHE = {}

version = __version__.split(".")
# checking for ^2.2.x

if not version[0] == "2":
    exit(1)




def GetUserLevel(username):
        if username in LVL_CASHE:
            return LVL_CASHE[username]
        else:
            usr = requests.get(f"https://api.meower.org/users/{username}").json()

            if usr.get("error", True):
                LVL_CASHE[username] = 0
                return 0
            
            LVL_CASHE[username] = usr['lvl']
            return usr['lvl']

GetUserLevel.clear = lambda: LVL_CASHE.clear() # type: ignore

class Cogs(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

   
            
    @command(args=1)
    def ban(self, ctx, username):
        
        user = db.users.find_one({"username": username})
        if user is None:
            ctx.reply(f"User @{username} not found")
            return

        del user["_id"]

        db.bans.insert_one({**user, "type": "username"})
        ctx.reply(f"Banned @{username}")

        requests.post(env["discord_webhook_url"], json={
            "content": f"Banned user {username}. Action by {ctx.message.user.username}\n\n <@{env['owner_discord_id']}>",
            "allowed_mentions": {
                "users": [env["owner_discord_id"]]
            }
        })

    @command(args=0)
    def help(self, ctx):
        nl = ",\n  " # getting around fstring syntax
        ctx.reply(f"prefix: @HookMod \ncommands are  {nl.join(list(meower.commands.keys()))}")

    @command(args=1)
    def ipban(self, ctx, username):
        if not GetUserLevel(ctx.message.user.username) >= 3 and ctx.message.user.username not in SPECIAL_ADMINS:
            ctx.reply("You dont have enough perms to ip ban for this meower bot")
            return
    
        user = db.users.find_one({"username": username})
        if user is None:
            ctx.reply(f"User @{username} not found")
            return
        
        del user["_id"]

        db.bans.insert_one({**user, "type": "ip", "banned_ip": user["ip"]})

        for ip in user["ip"]:
            db.bans.insert_one({**user, "type": "ip", "banned_ip": ip})
        
        ctx.reply(f"IPBanned @{username}")

        requests.post(env["discord_webhook_url"], json={
            "content": f"IPBanned user {username} with ip {user['ip']}. Action by {ctx.message.user.username}\n\n <@{env['owner_discord_id']}>",  
            "allowed_mentions": {
                "users": [env["owner_discord_id"]]
            }
        })

       
        
            
        
            

    @command(args=1)
    def guests( self, ctx, enable):
        if not GetUserLevel(ctx.message.user.username) >= 1 and ctx.message.user.username not in SPECIAL_ADMINS:
            ctx.reply("You dont have enough perms to enable/disable guests for this meower bot")
            return
        meower.DISABLE_GUESTS = not enable in ["enable", "1", "true", "True"]  # type: ignore
        ctx.reply(f"{'Enabled' if meower.DISABLE_GUESTS else 'Disabled'} Guests")

    @command(args=0)
    def clear_lvl_cache(self, ctx):
        GetUserLevel.clear()
        ctx.reply("Cleared Cache")

    @command(args=1)
    def restart(self, ctx):
        if not GetUserLevel(ctx.message.user.username) >= 4 and ctx.message.user.username not in SPECIAL_ADMINS:
            ctx.reply("You dont have enough perms to restart for this meower bot")
            return
        ctx.reply("Restarting")
        
        #close this thread, while also exiting the program
        os._exit(0)

    @command(args=0)
    def shutdown(self, ctx):
        if not GetUserLevel(ctx.message.user.username) >= 4 and ctx.message.user.username not in SPECIAL_ADMINS:
            ctx.reply("You dont have enough perms to shutdown for this meower bot")
            return
        ctx.reply("Shutting Down")
        
        #check for windows
        if os.name == "nt":
            #kill this process
            os._exit(0)

        #stop systemd service
        #check if running as root
        if os.geteuid() != 0:
            os.system(command="sudo systemctl stop meower-webhook.service")
        else:
            os.system("systemctl stop meower-webhook.service")

def on_message(message: Post , bot=meower):
    # assuming mb.py 2.2.0
    print(f"{message.user.username}: {message.data}")

    if message.user.username == env["username"]:
        return

    
    if not message.data.startswith(meower.prefix): return
    message.data = message.data.strip().split(meower.prefix, 1)[1].strip()

    if not shlex.split(str(message.data))[0] in meower.commands.keys():
        return
    
    if not GetUserLevel(message.user.username) >= 2 and  message.user.username not in SPECIAL_ADMINS:
        message.ctx.reply("You dont have perms to run commands for this meower bot") 
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
