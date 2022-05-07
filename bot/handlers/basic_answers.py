from typing import Union
from utils.keyboard import MainKeyboard, WalletsKeyboard
from handlers.handler_config import bot
from schemas.message import MessageEvent, MessageNew


def stop_message(message: Union[MessageNew, MessageEvent]):
    bot.send_message(message,
                     text="Возвращаюсь в главное меню.",
                     keyboard=MainKeyboard(True))

def error_message(message: Union[MessageNew, MessageEvent], error_message: str):
    bot.send_message(message,
                     text=f"Произошла ошибка: {error_message}",
                     keyboard=MainKeyboard(True))

def no_wallets_message(message: Union[MessageNew, MessageEvent]):
    bot.send_message(message,
                     text="Пока что у тебя нет кошельков.",
                     keyboard=WalletsKeyboard())

def wrong_input_message(message: Union[MessageNew, MessageEvent]):
    bot.send_message(message,
                     text="Неверный ввод. Выбери нужный пункт на клавиатуре.",
                     keyboard=MainKeyboard(True))

def not_registered_message(message: Union[MessageNew, MessageEvent]):
    bot.send_message(message,
                     text="Ты не зарегистрирован в системе",
                     keyboard=MainKeyboard())
