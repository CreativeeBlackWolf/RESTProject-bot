from fastapi import BackgroundTasks, FastAPI, Request, Response
from handlers import commands_handler, events_handler # noqa
from api.api_requests import UserAPIRequest
from utils.redis_utils import add_new_users, delete_key
from requests.exceptions import ConnectionError # noqa
from handlers.handler_config import bot
from json.decoder import JSONDecodeError
from time import sleep


app = FastAPI()
wallets_api = UserAPIRequest()


@app.on_event("startup")
async def startup():
    while True:
        try:
            users, status = wallets_api.get_users()
            break
        except ConnectionError:
            print(f"cannot get to API server ({wallets_api.users_url}). retry...")
            sleep(2)
    if status == 200:
        delete_key("registered_users")
        for u in users:
            add_new_users(u["vk_id"])
    bot.setup_bot()


@app.on_event("shutdown")
async def shutdown():
    pass


@app.post("/")
async def index(request: Request, background_task: BackgroundTasks):

    try:
        data = await request.json()
    except JSONDecodeError:
        return Response("not today", status_code=403)

    if data["type"] == "confirmation":
        return Response(bot.confirmation_code)

    # If the secrets match, then the message definitely came from our bot
    if data["secret"] == bot.secret:
        # Running the process in the background, because the logic can be complicated
        background_task.add_task(bot.handle_events, data)

    return Response("ok")
