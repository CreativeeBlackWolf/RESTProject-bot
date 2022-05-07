from schemas.message import (MessageEvent, MessageNew,
                                serialize_message, MessageEventTypes)
from typing import Any, Dict, List, Tuple, Union, Optional
from commands.step_handler import StepHandler
from commands.handler import BotCommands
from vk_api.utils import get_random_id
from secrets import token_urlsafe
from vk_api import vk_api


class Bot:
    def __init__(
        self,
        token: str,
        url: Optional[str] = None,
        group_id: Optional[str] = None,
        secret: Optional[str] = None,
        server_title: Optional[str] = None,
        commands: Optional[BotCommands] = None
    ) -> None:
        self.token = token
        self.api = vk_api.VkApi(token=self.token, api_version="5.131")
        self.vk = self.api.get_api()
        self.url = url
        self.group_id = group_id or self.__get_group_id()
        self.secret = secret or self.__generate_secret_key()
        self.server_title = server_title or "MyCallbackServer"
        self.commands = commands or BotCommands()
        self.steps = StepHandler()

    @staticmethod
    def __generate_secret_key() -> str:
        return token_urlsafe(32)

    def __get_group_id(self) -> None:
        return self.api.method("groups.getById", values={})[0]["id"]

    def get_confirmation_code(self) -> str:
        return self.api.method(
            "groups.getCallbackConfirmationCode",
            values={
                "group_id": self.group_id
            }
        )["code"]

    def get_callback_servers(self) -> List[Dict[str, Any]]:
        data = {"group_id": self.group_id}
        return self.api.method("groups.getCallbackServers", values=data)["items"]

    def find_server_id(self) -> Optional[int]:
        servers = self.get_callback_servers()

        if not servers:
            return None
        for server in servers:
            if server["url"] == self.url:
                return server["id"]
        return None

    def set_callback_settings(self, server_id: int, params: Dict[str, bool]):
        data = {
            "group_id": self.group_id,
            "server_id": server_id
        }
        data = data | params
        self.api.method("groups.setCallbackSettings", values=data)

    def add_callback_server(self) -> int:
        """returns server id"""
        data = {
            "group_id": self.group_id,
            "secret_key": self.secret,
            "url": self.url,
            "title": self.server_title
        }
        result = self.api.method("groups.addCallbackServer", values=data)
        return result["server_id"]

    def edit_callback_server(self, server_id: int, secret_key: Optional[str] = None) -> None:
        if secret_key is None:
            secret_key = self.secret

        data = {
            "group_id": self.group_id,
            "server_id": server_id,
            "url": self.url,
            "title": self.server_title,
            "secret_key": secret_key,
        }
        self.api.method("groups.editCallbackServer", values=data)

    def setup_bot(self) -> Tuple[str, str]:
        """
            returns confirmation code and secret
        """

        confirmation_code: str = self.get_confirmation_code()
        secret: str = self.secret

        server_id = self.find_server_id()

        if server_id is None:
            server_id = self.add_callback_server()
            self.set_callback_settings(server_id, params={
                "message_new": True,
                "message_edit": True,
                "message_event": True
            })
        else:
            self.edit_callback_server(server_id)
        return confirmation_code, secret

    def handle_events(self, data):
        message = serialize_message(data)
        # not handling messages from conversations
        if message.from_conversation:
            return

        if message.type == MessageEventTypes.MESSAGE_NEW:
            if message.peer_id in self.steps.handlers:
                self.steps.process_next_step(message.from_id, message)
            else:
                self.commands.call_command(message.text, message)
        elif message.type == MessageEventTypes.MESSAGE_EVENT:
            self.commands.call_event(message.payload["cmd"], message)

    def send_message(
        self,
        message: Union[MessageEvent, MessageNew],
        text: str,
        peer_id: int = None,
        keyboard: str = None
    ):
        """Sends a message and answers on event."""
        if isinstance(message, MessageEvent):
            self.vk.messages.sendMessageEventAnswer(event_id=message.event_id,
                                                    user_id=message.user_id,
                                                    peer_id=message.peer_id)
        if peer_id is None:
            peer_id = message.peer_id
        if not keyboard:
            self.vk.messages.send(peer_id=peer_id,
                                  random_id=get_random_id(),
                                  message=text)
        else:
            self.vk.messages.send(peer_id=peer_id,
                                  random_id=get_random_id(),
                                  message=text,
                                  keyboard=keyboard)