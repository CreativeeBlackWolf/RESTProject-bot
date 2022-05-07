from typing import Callable, Dict
from schemas.message import MessageNew
import logging


class StepHandler:
    def __init__(self) -> None:
        self.handlers: Dict[str, Callable] = {}

    def register_next_step_handler(
        self, user_id, func: Callable
    ) -> None:
        self.handlers[user_id] = func

    def get_next_handler(self, peer_id):
        return self.handlers.pop(peer_id, None)

    def process_next_step(self, peer_id, message: MessageNew):
        try:
            function = self.get_next_handler(peer_id)
            function(message)
        except Exception:
            logging.exception("An error has occured: ")
