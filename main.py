from threading import Thread
from os import environ as env
import os

from json import load, dump
import time
import string

from dotenv import load_dotenv


from flask import Flask
from flask import request, abort, jsonify

from MeowerBot import Client
from better_profanity import profanity

load_dotenv()

# so i dont need to deal with systemd being root.
os.chdir(os.path.dirname(__file__))


with open("banned_ips.json") as b_ips:
    BANNED_IPS = load(b_ips)

usernames_and_ips = {}


def get_remote_adress(request):
    if "X-Forwarded-For" in request.headers:
        return request.headers["X-Forwarded-For"].split(",")[-1]
    return request.access_route[-1]



from flask_cors import CORS, cross_origin



app = Flask(__name__)
app.DISABLE_GUESTS = False
app.meower = Client(env["username"], env["password"], debug=False)
app.meower.last_sent_perm = 0
app.meower.waiting_for_usr_input = {"usr": "", "waiting": False}


@app.before_request
def block_ips():
    if request.method == "GET":
        return
    ip = get_remote_adress(request)

    post_data = request.get_json()

    if post_data is None:
        abort(jsonify({"Error":"empty", "message":"no json found"}),400)

    if profanity.contains_profanity(post_data.get("username", "")):
        abort(jsonify({"Error":"username_profanity_error", "message":"Username contains profanity"}),403)

    post_data["username"] = post_data.get(
        "username", "guest" + str(ip).replace(".", "").replace(":", "")[:6]
    ).replace(" ", "_")

    if post_data['username'] == "":
      post_data['username'] = "guest" + str(ip).replace(".", "").replace(":", "")[:6]

    if app.DISABLE_GUESTS and post_data['username'].startswith("guest"):
        abort(jsonify({"Error":"guests_disabled"}),400)

    if not "post" in post_data:
        abort(jsonify({"Error":"missing", "key":"post"}),400)


    usernames_and_ips[post_data["username"]] = ip

    if ip in BANNED_IPS or post_data.get("username") in BANNED_IPS:
        abort(jsonify({"Error":"banned"}),403)  # Ip is banned from The API for this meower bot

    request.ip = ip


@app.route("/")
def root():
    return "Welcome to the meower websockets root page", 200


def post_to_chat(chat, data):

    if chat == "home":
        app.meower.send_msg(f"{data['username']}: {data['post']}")

    else:
        app.meower._wss.SendPacket(
            {
                "cmd": "direct",
                "val": {
                    "cmd": "post_chat",
                    "val": {
                        "chatid": chat,
                        "p": f"{data['username']}: {data['post']}",
                    },
                },
            }
        )
	


@app.route("/post/<chat>", methods=["POST"])
@cross_origin()
def post(chat):

    post_data = request.get_json()
    post_to_chat(chat, post_data)
    return "", 200

@app.after_request
def after_request(response: Response) -> Response:
    response.access_control_allow_origin = "*"
    return response

def save_db():
    with open("banned_ips.json", "w") as f:
        dump(BANNED_IPS, f)


def on_raw_packet(packet, lisn):
    cmd = packet["val"]
    app.meower.last_send_perms = 0
    if "mode" in cmd:
        if cmd["mode"] == "profile":
            app.meower.last_sent_perms = cmd["payload"]["lvl"]


def on_raw_msg(msg, lisn):
    print(f"msg: {msg['u']}: {msg['p']}")
    if msg["u"] == env["username"]:
        return

    if msg["u"] == "Discord":
        msg["u"] = msg["p"].split(":")[0]
        msg["p"] = msg["p"].split(":")[1].strip()

    app.meower._wss.sendPacket(
        {"cmd": "direct", "val": {"cmd": "get_profile", "val": msg["u"]}}
    )

    cmds = ["ipban", "ban", "help", "disable_guests", "enable_gusts"]

    time.sleep(3)  # waiting for the last req to go through and return

    args = msg["p"].split(" ")
    if not (args[0] == f"@{env['username']}"):
        return

    if (not len(args) >= 2) and (not args[1] in cmds):
        return

    if not (app.meower.last_send_perms >= 1) and (not (msg["u"] == "ShowierData9978")):
        app.meower.send_msg(
            f"@{msg['u']} you dont have the perms to run cmds for this bot"
        )
        return

    if args[1] == "ban":
        BANNED_IPS.append(args[2])
        app.meower.send_msg(f"Banned them")
        save_db()
    elif args[1] == "ipban":
        if not (app.meower.last_send_perms <= 2) and (
            not msg["u"] == "ShowierData9978"
        ):
            app.meower.send_msg(f"@{msg['p']} you dont have enough perms to ip ban")
            save_db()
            return
        if not app.meower.waiting_for_usr_input["waiting"]:
            app.meower.send_msg(
                f"@{msg['p']} if you are sure you want to do this, send the cmd again"
            )
            app.meower.waiting_for_user_input = {"waiting": True, "usr": msg["p"]}
        else:
            if not msg["u"] == app.meower.waiting_for_user_input["usr"]:
                app.meower.waiting_for_user_input = {"waiting": True, "usr": msg["p"]}
                return
            app.meower.send_msg(f"ip Banned them")
            app.meower.waiting_for_usr_input = {"usr": "", "waiting": False}
            BANNED_IPS.append(usernames_and_ips[args[2]])
            save_db()
    elif args[1] == 'guest_disable':
        if not (app.meower.last_send_perms <= 1) and (
            not msg["u"] == "ShowierData9978"
        ):
            app.meower.send_msg(f"@{msg['u']} you dont have enough perms to disable guests")
            return
        app.DISABLE_GUESTS = True
        app.meower.send_msg(f"@{msg['u']} guests have been disabled")
    elif args[1] == 'guest_enable':     
        if not (app.meower.last_send_perms <= 1) and (
            not msg["u"] == "ShowierData9978"
        ):
            app.meower.send_msg(f"@{msg['u']} you dont have enough perms to disable guests")
            return
            app.DISABLE_GUESTS = False
            app.meower.send_msg(f"@{msg['u']} guests have been enabled")
    elif args[1] == "help":
        app.meower.send_msg(f"@{msg['u']} here are my commands: {','.join(cmds)}")


app.meower.callback(on_raw_msg)
app.meower.callback(on_raw_packet)

if __name__ == "__main__":
    profanity.load_censor_words()
    t = Thread(target=app.run, kwargs={"host": "0.0.0.0"})
    t.start()

    try:
        app.meower.start()
    except:
        pass
    finally:
        os.system(f"kill -9 {os.getpid()}")
        t.join()
