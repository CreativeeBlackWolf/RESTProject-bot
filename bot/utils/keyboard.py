from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from schemas.models import Wallet
from typing import List


#region Buttons
def back_button(keyboard: VkKeyboard) -> VkKeyboard:
    keyboard.add_line()
    keyboard.add_callback_button(label="Назад",
                                 color=VkKeyboardColor.NEGATIVE,
                                 payload={"cmd": "back_button"})

    return keyboard
#endregion

#region Keyboards
def get_empty_keyboard():
    return VkKeyboard.get_empty_keyboard()

def main_keyboard(registered_user: bool = False):
    keyboard = VkKeyboard()
    keyboard.add_button(label="Кошельки", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(label="Транзакции", color=VkKeyboardColor.POSITIVE)

    if not registered_user:
        keyboard.add_line()
        keyboard.add_callback_button(label="Зарегистрироваться",
                                     payload={"cmd": "register_user"},
                                     color=VkKeyboardColor.NEGATIVE)

    return keyboard.get_keyboard()

def wallets_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_callback_button(label="Создать кошелёк",
                                 color=VkKeyboardColor.PRIMARY,
                                 payload={"cmd": "create_wallet"})

    keyboard.add_callback_button(label="Просмотреть кошельки",
                                 color=VkKeyboardColor.SECONDARY,
                                 payload={"cmd": "user_wallets"})
    keyboard.add_line()
    keyboard.add_callback_button(label="Редактировать кошельки",
                                 color=VkKeyboardColor.PRIMARY,
                                 payload={"cmd": "edit_wallets"})

    keyboard = back_button(keyboard)
    return keyboard.get_keyboard()

def transactions_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_callback_button(label="Исходящие транзакции",
                                 payload={"cmd": "show_outcoming_transactions"},
                                 color=VkKeyboardColor.PRIMARY)
    keyboard.add_callback_button(label="Входящие транзакции",
                                 payload={"cmd": "show_incoming_transactions"},
                                 color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_callback_button(label="Перевести деньги",
                                 payload={"cmd": "make_transaction"},
                                 color=VkKeyboardColor.PRIMARY)

    keyboard = back_button(keyboard)
    return keyboard.get_keyboard()

def edit_wallets_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_callback_button(label="Редактировать кошелёк",
                                 color=VkKeyboardColor.PRIMARY,
                                 payload={"cmd": "edit_wallet"})

    keyboard.add_callback_button(label="Удалить кошелёк",
                                 color=VkKeyboardColor.NEGATIVE,
                                 payload={"cmd": "delete_wallet"})

    keyboard = back_button(keyboard)
    return keyboard.get_keyboard()

def user_wallets_keyboard(wallets: List[Wallet], show_balance: bool=True):
    """
    Display keyboard with given wallets, so the user can select one.

    Parameters
    ----------
    `show_balance`
        Display the balance with wallet name.
    """
    keyboard = VkKeyboard(one_time=True)
    for k, wallet in enumerate(wallets):
        payload = {}

        if not show_balance:
            label = wallet.name
        else:
            if len(wallet.name) > 20:
                wallet.name = wallet.name[:17] + "..."
            label = label=f"{wallet.name} | Баланс: {wallet.balance}"
            payload["balance"] = wallet.balance

        payload["UUID"] = str(wallet.pk)

        keyboard.add_button(label=label,
                            color=VkKeyboardColor.POSITIVE,
                            payload=payload)

        # do not add line if iterated wallet is last
        if k != len(wallets) - 1:
            keyboard.add_line()

    return keyboard.get_keyboard()
#endregion
