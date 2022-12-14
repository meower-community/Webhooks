import time
import string
import shlex

from json import load, dump
from flask import Flask, request, abort, jsonify
from flask_cors import CORS

from better_profanity import profanity




app = Flask(__name__)
app.CORS = CORS(app, resources=r'*')

usernames_and_ips = {}

def get_remote_adress(request):
    if "X-Forwarded-For" in request.headers:
        return request.headers["X-Forwarded-For"].split(",")[-1]
    return request.access_route[-1]

@app.before_request
def block_ips():
    if not request.method == "POST": return

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

    if app.meower.DISABLE_GUESTS and post_data['username'].startswith("guest"):
        abort(jsonify({"Error":"guests_app.meower.disabled"}),400)

    if not "post" in post_data:
        abort(jsonify({"Error":"missing", "key":"post"}),400)

    usernames_and_ips[post_data["username"]] = {"ip": ip, "pfp": post_data.get("pfp", 0)}


    if ip in app.BANNED_IPS or post_data.get("username") in app.BANNED_IPS:
        abort(jsonify({"Error":"banned"}),403)  # Ip is banned from The API for this meower bot

    request.ip = ip


@app.route("/")
def root():
    return "Welcome to the meower websockets root page", 200

@app.route("/pfps/<username>")
def get_pfp(username):
    if username not in usernames_and_ips:
        return username, 404
    
    return usernames_and_ips[username]['pfp']

def post_to_chat(chat, data):
    app.meower.send_msg(f"{data['username']}: {data['post']}", to=chat)
	


@app.route("/post/<chat>", methods=["POST"])
def post(chat):

    post_data = request.get_json()
    post_to_chat(chat, post_data)
    return "", 204


@app.after_request
def after_request_func(response):
        origin = request.headers.get('Origin')
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Headers', 'x-csrf-token')
            response.headers.add('Access-Control-Allow-Methods',
                                'GET, POST, OPTIONS, PUT, PATCH, DELETE')
            if origin:
                response.headers.add('Access-Control-Allow-Origin', origin)
        else:
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            if origin:
                response.headers.add('Access-Control-Allow-Origin', origin)

        return response


if __name__ == "__main__":
    raise ImportError("web.py should be a module, not a main file")