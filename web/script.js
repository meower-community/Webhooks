
const ws = new WebSocket("wss://server.meower.org/")
const login = document.getElementById("signin")
const create_fourm = document.getElementById("create")
const create_error = document.getElementById("create_error")
const dashbord = document.getElementById("dash")

let username = null;
let password = null;
let connected = false;
let token = null;

const events = new class {
    constructor() {
        this.callbacks = {}
    }

    on(event, callback) {
        this.callbacks[event] = callback
    }

    emit(event, ...args) {
        this.callbacks[event](...args)
    }
}

function dologin() {
    if (username === null) return
    if (connected) return;

    ws.send(JSON.stringify({
        cmd: "direct",
        val: {
            cmd: "authpswd",
            val: {
                username: username,
                pswd: password
            }
        }
    }))
}

login.onsubmit = (event) => {
    event.preventDefault();

    username = document.getElementById("login_username").value;
    password = document.getElementById("login_password").value;
    if (!connected) dologin()
}


ws.onopen = () => {
       ws.send(JSON.stringify({
			cmd: "direct",
	  	    val: {
                cmd: "type",
                val: "js"
            }
       }))

       dologin();
}

ws.onmessage = (event) => {
    const packet = JSON.parse(event.data);

    if (packet.cmd === "pmsg") {
        if (packet.origin !== "Webhooks")
            return

        if (!packet.val.hasOwnProperty("status"))
            return // bot packets

        events.emit(`${packet.val.listener}`, packet.val)
    } else if (packet?.val?.mode === "auth") {
        connected = true;
        token = packet.val.payload.token;
        login.style.display = "none";
        dashbord.style.display = "block";
    }
}

let listener_id = 0;

create_fourm.onsubmit = (event) => {
    event.preventDefault();
    const chatid = document.getElementById("create_chat").value;
    const pfp = document.getElementById("create_pfp").value;
    const lisener = listener_id++;

    events.on(`${lisener}`, (val) => {
        if (val.error)
            return create_error.innerText = val.human;


        navigator.clipboard.writeText(`https://webhooks.meower.org/webhook/${val.id}/${val.token}/${val.chat}/post`).then(
            () => {
                create_error.innerText = "Your Webhook has been copied!"
            },
            () => {
                create_error.innerText = "Uh oh, please let us copy to clipbord"
            }

        )
    })

    fetch(`https://api.meower.org/chats/${chatid}/members/Webhooks`, {
        method: "PUT",
        headers: {
            "token": token,
            "username": username
        }
    }).then(resp => {
        if (!resp.ok && !(chatid === "home" || chatid === "livechat")) {
            create_error.innerText = `Unexpected HTTP Statuscode: ${resp.status}`
            return;
        }

        ws.send(JSON.stringify({
            "cmd": "pmsg",
            "id": "Webhooks",
            "val": {
                "cmd": "create",
                "val": {
                    "chat": chatid,
                    "pfp": pfp
                },
                "listener": lisener
            }
        }))
    })

}
