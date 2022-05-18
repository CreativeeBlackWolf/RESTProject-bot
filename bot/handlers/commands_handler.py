from handlers.basic_answers import not_registered_message
from utils.keyboard import MainKeyboard, WalletsKeyboard, TransactionsKeyboard
from utils.redis_utils import RedisUtils
from handlers.handler_config import bot
from schemas.message import MessageNew


redis = RedisUtils()


@bot.commands.default_handler
def default(message: MessageNew):
    bot.send_message(message,
                     text="что.",
                     keyboard=MainKeyboard(redis.is_registered_user(message.from_id)))


@bot.commands.handle_command(text="ping")
def hello_command(message: MessageNew):
    bot.send_message(message,
                     text="pong!")


@bot.commands.handle_command(text="Кошельки")
def wallets_keyboard(message: MessageNew):
    if not redis.is_registered_user(message.from_id):
        not_registered_message(message)
        return
    bot.send_message(message,
                    text="Методы кошельков",
                    keyboard=WalletsKeyboard())


@bot.commands.handle_command(text="Транзакции")
def transactions_keyboard(message: MessageNew):
    if not redis.is_registered_user(message.from_id):
        not_registered_message(message)
        return
    bot.send_message(message,
                     text="Методы транзакций",
                     keyboard=TransactionsKeyboard())
