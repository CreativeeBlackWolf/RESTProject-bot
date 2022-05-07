from handlers.basic_answers import error_message, no_wallets_message
from utils.keyboard import (EditWalletsKeyboard, EmptyKeyboard, MainKeyboard,
                                UserWalletsKeyboard, WalletsKeyboard,
                                TransactionsKeyboard)
from api.api_requests import TransactionsAPIRequest, UserAPIRequest, WalletAPIRequest
from handlers.wallet_steps import delete_step, edit_choice_step, process_new_wallet
from handlers.transaction_steps import transactions_to_or_whence_step
from utils.redis_utils import is_registered_user, add_new_users
from schemas.message import MessageEvent
from handlers.handler_config import bot
from datetime import datetime


user_api = UserAPIRequest()
wallet_api = WalletAPIRequest()
transaction_api = TransactionsAPIRequest()


@bot.commands.handle_event(event="back_button")
def back_button_event(event: MessageEvent):
    bot.send_message(event,
                     text="Возвращаемся в главное меню.",
                     keyboard=MainKeyboard(is_registered_user(event.user_id)))


@bot.commands.handle_event(event="register_user")
def register_user_event(event: MessageEvent):
    user = bot.vk.users.get(user_ids=event.user_id)[0]
    _, status = user_api.create_user(event.user_id, user["first_name"] + " " + user["last_name"])
    if status == 201:
        add_new_users(str(event.user_id))
        bot.send_message(event,
                         text="Ты успешно зарегистрировался!",
                         keyboard=MainKeyboard(True))
    elif status == 400:
        bot.send_message(event,
                         text="Ты уже зарегистрирован.",
                         keyboard=MainKeyboard(True))
    else:
        error_message(event, status)


@bot.commands.handle_event(event="user_wallets")
def get_user_wallets(event: MessageEvent):
    wallets, status = wallet_api.get_user_wallets(event.user_id)
    if status == 200:
        if not wallets:
            no_wallets_message(event)
        else:
            message = "Твои кошельки:\n\n"
            for k, wallet in enumerate(wallets):
                message += \
f"""
{k+1}) Уникальный идентификатор: {wallet.pk}
| Название: {wallet.name}
| Баланс: {wallet.balance}
"""
            bot.send_message(event,
                             text=message,
                             keyboard=WalletsKeyboard())
    else:
        error_message(event, status)


@bot.commands.handle_event(event="create_wallet")
def create_wallet(event: MessageEvent):
    bot.send_message(event,
                     text="Придумай имя своему кошельку.",
                     keyboard=EmptyKeyboard())
    bot.steps.register_next_step_handler(event.user_id, process_new_wallet)


@bot.commands.handle_event(event="make_transaction")
def make_transaction(event: MessageEvent):
    wallets, status = wallet_api.get_user_wallets(event.user_id)
    if status == 200:
        if wallets:
            bot.send_message(event,
                             text="Выбери свой кошелёк из списка",
                             keyboard=UserWalletsKeyboard(wallets))
            bot.steps.register_next_step_handler(event.user_id, transactions_to_or_whence_step)
        else:
            no_wallets_message(event)


@bot.commands.handle_event(event=["show_outcoming_transactions", "show_incoming_transactions"])
def show_latest_transactions(event: MessageEvent):
    incoming = True if event.payload["cmd"] == "show_incoming_transactions" else False
    user_transactions, status = transaction_api.get_user_transactions(
        event.user_id,
        incoming=incoming
    )
    if status == 200:
        if not user_transactions:
            message = "Ты пока что не совершал переводов." if not incoming \
                      else "Тебе пока что не отправляли переводов."
        else:
            message = "Переводы:\n-----------------"
            for transaction in user_transactions:
                date = datetime.strptime(transaction.date, "%Y-%m-%dT%H:%M:%S.%f%z")
                formatted_date = date.strftime("%d %B %Y %H:%M:%S")
                if incoming:
                    message += f"\nОтправитель: {transaction.from_wallet_user}"
                else:
                    message += f"""
Из кошелька: {transaction.from_wallet_name}
Кому: {transaction.to_wallet_user if transaction.to_wallet_user is not None
       else "<Сторонний сервис>"}"""

                message += f"""
Куда: {transaction.whence if transaction.whence is not None
       else "на кошелёк " + transaction.to_wallet_name}
Размер платежа: {transaction.payment}
Когда: {formatted_date}
Комментарий к переводу: {transaction.comment if transaction.comment
                         else "<Без комментария>"}
-----------------"""

        bot.send_message(event,
                         text=message,
                         peer_id=event.user_id,
                         keyboard=TransactionsKeyboard())


@bot.commands.handle_event(event="edit_wallets")
def show_edit_keyboard(event: MessageEvent):
    wallets, status = wallet_api.get_user_wallets(event.user_id)
    if status == 200:
        if wallets:
            bot.send_message(event,
                             text="Редактирование кошельков.",
                             keyboard=EditWalletsKeyboard())
        else:
            no_wallets_message(event)


@bot.commands.handle_event(event=["delete_wallet", "edit_wallet"])
def edit_user_wallet(event: MessageEvent):
    wallets, status = wallet_api.get_user_wallets(event.user_id)
    if not wallets:
        no_wallets_message(event)
        return
    if status == 200:
        bot.send_message(event,
                         text="Выбери кошелёк из списка",
                         keyboard=UserWalletsKeyboard(wallets, show_balance=False))
        if event.payload["cmd"] == "edit_wallet":
            bot.steps.register_next_step_handler(event.user_id, edit_choice_step)
        else:
            bot.steps.register_next_step_handler(event.user_id, delete_step)
