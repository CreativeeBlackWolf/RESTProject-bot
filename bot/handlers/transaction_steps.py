from api.api_requests import WalletAPIRequest, TransactionsAPIRequest
from utils.keyboard import main_keyboard, user_wallets_keyboard
from utils.redis_utils import RedisUtils
from handlers.basic_answers import error_message, stop_message, wrong_input_message
from handlers.handler_config import bot
from schemas.message import MessageNew
from utils.check import find_urls
import json


wallets_api = WalletAPIRequest()
redis = RedisUtils()
transactions_api = TransactionsAPIRequest()
transactions = {}


def transactions_to_or_whence_step(message: MessageNew):
    if message.text.lower() in ("стоп", "stop"):
        stop_message(message)
        return

    if message.payload:
        payload = json.loads(message.payload)
    else:
        wrong_input_message(message)
        return

    transactions[message.from_id] = {
        "from_wallet": payload["UUID"],
        "balance": payload["balance"]
    }
    bot.send_message(message,
        text="Введи ID пользователя в ВК (можно ссылкой) или куда ты хочешь перевести деньги."
    )
    bot.steps.register_next_step_handler(message.from_id, transactions_check_vk_id)

def transactions_check_vk_id(message: MessageNew):
    try:
        urls = find_urls(message.text, template="vk.com/")
        if urls:
            #                          taking only first url
            user = bot.vk.users.get(user_ids=urls[0].split("/")[-1])
            if not user:
                bot.send_message(message,
                    text="Ссылка введена неверно или такого пользователя не существует",
                    keyboard=main_keyboard(True)
                )
                return
            user_id = user[0]["id"]
        else:
            user_id = int(message.text)

        if not redis.is_registered_user(user_id):
            bot.send_message(message,
                             text="Такой пользователь не зарегистрирован в системе. Возвращаюсь.",
                             keyboard=main_keyboard(True))
            return

        wallets, status = wallets_api.get_user_wallets(user_id)
        if status == 200:
            if not wallets:
                bot.send_message(message,
                                 text="У пользователя с таким ID нет кошельков. Возвращаюсь",
                                 keyboard=main_keyboard(True))
                return
            bot.send_message(message,
                             text="Выбери кошелёк получателя.",
                             keyboard=user_wallets_keyboard(wallets, show_balance=False))

            transactions[message.from_id]["recipient_id"] = user_id
            bot.steps.register_next_step_handler(message.from_id, transactions_payment_step)
    except ValueError:
        transactions[message.from_id]["recipient_id"] = None
        transactions_payment_step(message)

def transactions_payment_step(message: MessageNew):
    if message.text.lower() in ("стоп", "stop"):
        stop_message(message)
        return
    # if uuid is given
    if message.payload:
        payload = json.loads(message.payload)
        transactions[message.from_id]["to_wallet"] = payload["UUID"]
        transactions[message.from_id]["whence"] = None
    else:
        transactions[message.from_id]["to_wallet"] = None
        transactions[message.from_id]["whence"] = message.text
    bot.send_message(message,
                     text="Сколько перевести?")
    bot.steps.register_next_step_handler(message.from_id, transactions_comment_step)

def transactions_comment_step(message: MessageNew):
    if message.text.lower() in ("стоп", "stop"):
        stop_message(message)
        return
    try:
        transactions[message.from_id]["payment"] = int(message.text)
        if transactions[message.from_id]["payment"] <= 0:
            raise ValueError
        if transactions[message.from_id]["balance"] < transactions[message.from_id]["payment"]:
            bot.send_message(message,
                             text="Недостаточно средств. Возвращаюсь.",
                             keyboard=main_keyboard(True))
            return
    except ValueError:
        bot.send_message(message,
                         text="Количество переводимых средств должно быть целым положительным числом.",
                         keyboard=main_keyboard(True))
        return
    bot.send_message(message,
                     text="Оставьте комментарий (введите \"нет\", если не нужно).")
    bot.steps.register_next_step_handler(message.peer_id, transactions_final_step)

def transactions_final_step(message: MessageNew):
    if message.text.lower() in ("стоп", "stop"):
        stop_message(message)
        return
    if message.text.lower() not in ("нет", "н", "no", "n"):
        transactions[message.from_id]["comment"] = message.text
        if len(transactions[message.from_id]["comment"]) > 128:
            bot.send_message(message,
                             text="Количество символов в комментарии не должно привышать 128 символов",
                             keyboard=main_keyboard(True))
            return
    else:
        transactions[message.from_id]["comment"] = None
    transaction_data = transactions.pop(message.from_id, None)
    transaction, status = transactions_api.make_transaction(**transaction_data)
    if status == 201:
        bot.send_message(message,
                         text="Перевод отправлен!",
                         keyboard=main_keyboard(True))

        # if the payment was sent to the user
        if transaction_data["recipient_id"] is not None:
            recipient = bot.vk.users.get(user_ids=message.from_id,
                                     name_case="gen")[0]
            sender_name = f"{recipient['first_name']} {recipient['last_name']}"
            text = \
f"""Пополнение `{transaction.to_wallet_name}`: +{transaction.payment} от {sender_name}
Комментарий к переводу: {transaction.comment}
"""
            bot.send_message(message,
                             text=text,
                             peer_id=transaction_data["recipient_id"])
    elif status == 400:
        error_message(message, transaction)
