from handlers.basic_answers import error_message, stop_message, wrong_input_message
from utils.keyboard import edit_wallets_keyboard, wallets_keyboard
from api.api_requests import WalletAPIRequest
from utils.redis_utils import RedisUtils
from handlers.handler_config import bot
from schemas.message import MessageNew
import json


wallets_api = WalletAPIRequest()
redis = RedisUtils()


def process_new_wallet(message: MessageNew):
    if message.text.lower() in ["стоп", "stop"]:
        stop_message(message)
        return
    if len(message.text) > 32:
        bot.send_message(message,
                         text="Длина названия кошелька должна быть менее 32 символов.",
                         keyboard=wallets_keyboard())
        return
    _, status = wallets_api.create_new_wallet(message.from_id, message.text)
    if status == 201:
        bot.send_message(message,
                         text=f"Кошелёк \"{message.text}\" успешно создан!",
                         keyboard=wallets_keyboard())
    elif status == 400:
        message = "Кошелёк с таким названием уже существует. Придумай что-нибудь другое..."
        bot.send_message(message,
                         text=message,
                         keyboard=wallets_keyboard())
    else:
        error_message(message, status)

def edit_choice_step(message: MessageNew):
    if message.text.lower() in ["stop", "стоп"]:
        stop_message(message)
        return
    if message.payload:
        payload = json.loads(message.payload)
        redis.add_wallet_step_data(message.from_id, "wallet", payload["UUID"])
        bot.send_message(message,
                         text="Придумай имя своему кошельку.")
        bot.steps.register_next_step_handler(message.from_id, edit_final_step)
    else:
        wrong_input_message(message)

def edit_final_step(message: MessageNew):
    if message.text.lower() in ["stop", "стоп"]:
        stop_message(message)
        return
    wallet = redis.get_wallet_step_data(message.from_id)
    if len(message.text) > 32:
        bot.send_message(message,
                         text="Длина названия кошелька должна быть менее 32 символов.",
                         keyboard=edit_wallets_keyboard())
        return
    _, status = wallets_api.edit_user_wallet(wallet, message.text, message.from_id)
    if status == 200:
        bot.send_message(message,
                         text=f"Кошелёк `{wallet}` успешно переименован в {message.text}",
                         keyboard=edit_wallets_keyboard())
    else:
        error_message(message, status)

def delete_step(message: MessageNew):
    if message.text.lower() in ["stop", "стоп"]:
        stop_message(message)
        return
    if message.payload:
        payload = json.loads(message.payload)
        wallet = payload["UUID"]
        status = wallets_api.delete_wallet(wallet)
        if status == 204:
            bot.send_message(message,
                             text=f"Кошелёк `{wallet}` успешно удалён.",
                             keyboard=edit_wallets_keyboard())
        else:
            error_message(message, status)
    else:
        wrong_input_message(message)
