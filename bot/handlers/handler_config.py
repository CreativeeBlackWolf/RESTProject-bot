from bot import Bot
from settings import get_bot_settings


config = get_bot_settings().dict()
bot = Bot(**config)
