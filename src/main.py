import asyncio
import subprocess
import sys

import requests
from MeowerBot import CallBackIds
from MeowerBot.command import callback, command
from MeowerBot.ext.help import Help

from sys import path


path.insert(0, "../")

from dotenv import load_dotenv
load_dotenv()

from os import environ as env


from bot import Webhooks
from database import Database


# noinspection PyBroadException
class BridgeHelp(Help):
    @command(name="help", args=1)
    async def help(self, ctx, page: int = 0):
        if page >= len(self.pages):
            page = len(self.pages) - 1

        await ctx.send_msg("Webhooks: " + self.pages[page])


    @callback(CallBackIds.login)
    @staticmethod
    async def _login(token):
        self = BridgeHelp.__instance__
        assert self is not None
        resp = None
        while resp is None:  # fixes a race condition on host machine
            try:
                resp = requests.post("http://localhost:10000/internal/token", data=token, timeout=1)
            except:
                await asyncio.sleep(1)

        if self._generated:
            return

        self._generated = True
        self.bot.logger.info("Generating Help")
        self.generate_help()  # generate help on login, bugfix for default prefix, and people being dumb


db = Database(env.get("DB_URL", "mongodb://localhost:27017"), env.get("DB_NAME", "webhooks"))

bot = Webhooks(prefix="@Webhooks")
bot.add_app(db)
bot.register_cog(BridgeHelp(bot, disable_command_newlines=True))





if __name__ == "__main__":
    proc = subprocess.Popen([sys.executable, "src/web.py"])
    bot.run(env["uname"], env["pswd"])
    proc.wait()