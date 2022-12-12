from threading import Thread
from os import environ as env
import os

from json import load, dump
import time
import string

from dotenv import load_dotenv

from MeowerBot import Bot, __version__
from better_profanity import profanity
from sys import exit

load_dotenv()
import shlex

from web import app
import web

# so i dont need to deal with systemd being root.
os.chdir(os.path.dirname(__file__))


with open("banned_ips.json") as b_ips:
    BANNED_IPS = load(b_ips)




def get_remote_adress(request):
    if "X-Forwarded-For" in request.headers:
        return request.headers["X-Forwarded-For"].split(",")[-1]
    return request.access_route[-1]

meower = Bot(debug=False)
meower.DISABLE_GUESTS = False
app.meower = meower
app.BANNED_IPS = BANNED_IPS

meower.waiting_for_usr_input = {"usr": "", "waiting": False, "banning": ""}

SPECIAL_ADMINS = ["ShowierData9978"]

version = __version__.split(".")

# checking for ^2.2.x

if not version[0] == "2":
    exit(1)

if not int(version[1]) >= 2:
    exit(1)

def save_db():
    with open("banned_ips.json", "w") as f:
        dump(BANNED_IPS, f)


@bot.command(args=1)
def ban(ctx, username):
    BANNED_IPS.append(username)
    save_db()
    ctx.reply(f"banned @{username}")

@bot.command(args=0)
def help(ctx):
    ctx.reply(f"prefix: @Webhooks \n commands: {meower.commands.keys()}")

@bot.command(args=1)
def ipban(ctx, username):
    if not ctx.message.user.lvl >= 3 and ctx.message.user.username not in SPECIAL_ADMINS:
         ctx.reply("You dont have enough perms to ip ban for this bot")
         return
    
    if not username in web.usernames_and_ips:
        ctx.reply("Cant Find that user in my ip table ):")
        return

    if meower.waiting_for_user_input.get("usr", "") == ctx.message.user.username and waiting_for_user_input['banning'] == username:
        BANNED_IPS.append(web.usernames_and_ips[username]['ip'])
        save_db()
    else:
        ctx.reply("Are you sure you want to do this, if your sure run the command again")
        meower.waiting_for_user_input = {"usr": ctx.message.user.username, "banning": username}

@bot.command(args=1)
def guests(ctx, enable):
    meower.DISABLE_GUESTS = not enable in ["enable", "1", "true", "True"] 
    ctx.reply(f"Set Guests to {enable}")

def on_message(message):
    # assuming mb.py 2.2.0

    if message.user.username == env["username"]:
        return

    
    if not message.data.startswith(meower.prefix): return
    message.data = message.data.split(meower.prefix, 1)[1]

    if not shlex.split(str(message)) in meower.commands:
        return
    
    if not message.user.lvl >= 2 and  message.user.username not in SPECIAL_ADMINS:
        message.ctx.reply("You dont have perms to run commands for this bot") 
        return
    
    meower.run_command(message)


meower.callback(on_message, cbid="message")

if __name__ == "__main__":
    profanity.load_censor_words()
    t = Thread(target=app.run, kwargs={"host": "0.0.0.0"})
    t.start()

    try:
        meower.start(env['username'], env['password'])
    except:
        pass
    finally:
        os.system(f"kill -9 {os.getpid()}")
        t.join()
