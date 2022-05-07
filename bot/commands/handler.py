from typing import Callable, Collection, Dict, Union
from schemas.message import MessageEvent, MessageNew


class BotCommands:
    def __init__(self):
        # {"command_text": func}
        self._commands: Dict[str, Callable] = {}
        self._events: Dict[str, Callable] = {}
        self._default_message_handler: Callable = None


    @property
    def commands(self):
        return self._commands

    @property
    def events(self):
        return self._events

    @property
    def default_message_handler(self):
        """Function that called every time there is no handler for received message"""
        return self._default_message_handler

    @default_message_handler.setter
    def default_message_handler(self, value: Callable):
        if callable(value):
            self._default_message_handler = value
        else:
            raise ValueError(f"Handler must be Callable, not {type(value)}")

    def default_handler(self, func: Callable):
        """Decorator to define default message handler"""
        self._default_message_handler = func

    def handle_command(self, text: str):
        """Decorator for function that should handle `message_text` event type."""
        def wrapper(func: Callable):
            self._commands.update({text: func})
        return wrapper

    def handle_event(self, event: Union[str, Collection]):
        """Decorator for function that should handle `message_event` event type."""
        def wrapper(func: Callable):
            if isinstance(event, str):
                self._events.update({event: func})
            else:
                for e in event:
                    self._events.update({e: func})
        return wrapper

    def call_command(self, text, message: MessageNew):
        try:
            function = self.commands[text]
            function(message)
        except KeyError:
            if self.default_message_handler is not None:
                self.default_message_handler(message)

    def call_event(self, event: str, message: MessageEvent):
        try:
            function = self.events[event]
            function(message)
        except KeyError:
            return
