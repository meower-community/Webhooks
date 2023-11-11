import asyncio
from MeowerBot import Bot
from sanic import Sanic

from web import webhook_bp, loaded
from dotenv import load_dotenv
load_dotenv()

from os import environ as env


from bot import Webhooks
from database import Database



app = Sanic("Webhooks")
app.ctx.bot = Webhooks(prefix="@Webhooks", app=app)
app.ctx.db = Database(env["DB_URL"], env["DB_NAME"])


app.blueprint(webhook_bp)

bot: Bot = app.ctx.bot
loaded(bot)


async def main():
    loop = asyncio.get_event_loop()

    # pylint: disable=unused-variable
    app_task = loop.create_task(app.create_server(host="0.0.0.0", port=8000))  # noqa(E501)

    await bot.start(env["uname"], env["pswd"])

if __name__ == "__main__":
    asyncio.run(main())
