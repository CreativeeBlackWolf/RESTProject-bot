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
    """
    Read wallet information and register recipient check step.
    """
    if message.text.lower() in ("стоп", "stop"):
        stop_message(message)
        return

    if message.payload:
        payload = json.loads(message.payload)
    else:
        wrong_input_message(message)
        return

    redis.add_transaction_step_data(message.from_id, "from_wallet", payload["UUID"])
    redis.add_transaction_step_data(message.from_id, "balance", payload["balance"])
    bot.send_message(message,
        text="Введи ID пользователя в ВК (можно ссылкой) или куда ты хочешь перевести деньги."
    )
    bot.steps.register_next_step_handler(message.from_id, transactions_check_vk_id)

def transactions_check_vk_id(message: MessageNew):
    """
    Read the recipient, 
    check if the given user is registered and has wallets,
    and register payment step.
    """
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

            redis.add_transaction_step_data(message.from_id, "recipient_id", user_id)
            bot.steps.register_next_step_handler(message.from_id, transactions_payment_step)
    
    except ValueError:
        redis.add_transaction_step_data(message.from_id, "recipient_id", None)
        transactions_payment_step(message)

def transactions_payment_step(message: MessageNew):
    """
    Read the recipient wallet information,
    display payment requirement and register comment step.
    """
    if message.text.lower() in ("стоп", "stop"):
        stop_message(message)
        return

    wallet_UUID = None
    whence = None
    # if uuid is given
    if message.payload:
        payload = json.loads(message.payload)
        wallet_UUID = payload["UUID"]

    else:
        whence = message.text

    redis.add_transaction_step_data(message.from_id, "to_wallet", wallet_UUID)
    redis.add_transaction_step_data(message.from_id, "whence", whence)

    bot.send_message(message,
                     text="Сколько перевести?")
    bot.steps.register_next_step_handler(message.from_id, transactions_comment_step)

def transactions_comment_step(message: MessageNew):
    """
    Read a payment,
    display comment requirement and register final transaction step.
    """
    if message.text.lower() in ("стоп", "stop"):
        stop_message(message)
        return
    try:
        redis.add_transaction_step_data(message.from_id, "payment", int(message.text))
        if int(message.text) <= 0:
            raise ValueError

    except ValueError:
        bot.send_message(message,
                         text="Количество переводимых средств должно быть целым положительным числом.",
                         keyboard=main_keyboard(True))
        return
    bot.send_message(message,
                     text="Оставьте комментарий (введите \"нет\", если не нужно).")
    bot.steps.register_next_step_handler(message.peer_id, transactions_final_step)

def transactions_final_step(message: MessageNew):
    """
    Read comment, finilaze transaction data and make a transaction.
    """

    if message.text.lower() in ("стоп", "stop"):
        stop_message(message)
        return
    
    transaction_data = redis.get_transaction_step_data(message.from_id)

    if message.text.lower() not in ("нет", "н", "no", "n"):
        comment = message.text
        if len(comment) > 128:
            bot.send_message(message,
                             text="Количество символов в комментарии не должно привышать 128 символов",
                             keyboard=main_keyboard(True))
            return
    else:
        comment = None
    
    transaction, status = transactions_api.make_transaction(**transaction_data, comment=comment)
    
    if transaction_data["balance"] < transaction_data["payment"]:
        bot.send_message(message,
                        text="Недостаточно средств для перевода. Возвращаюсь.",
                        keyboard=main_keyboard(True))
        return
    
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
