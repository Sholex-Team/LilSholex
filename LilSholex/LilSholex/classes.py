from LilSholex.decorators import fix
from urllib.parse import urlencode
import json
from persianmeme.models import User as PersianMemeUser
from typing import Union, Tuple
from aiohttp import ClientSession
from abc import ABC, abstractmethod
from asgiref.sync import sync_to_async


class Base(ABC):
    database: PersianMemeUser

    def __init__(
            self,
            token: str,
            chat_id: Union[int, None],
            instance: Union[PersianMemeUser, None],
            session: ClientSession
    ):
        self.token = token
        self.session = session
        self.chat_id = chat_id
        self.__instance = instance

    @abstractmethod
    def get_user(self) -> Tuple[PersianMemeUser, bool]:
        pass

    def __await__(self):
        if not self.chat_id:
            assert self.__instance, 'Instance must be passed when chat id isn\'t !'
            self.database = self.__instance
        else:
            self.database, created = yield from self.get_user().__await__()
        return self

    @fix
    async def send_message(
            self,
            text: str,
            /,
            reply_markup: dict = '',
            reply_to_message_id: int = '',
            parse_mode: str = None,
            disable_web_page_preview: bool = True,
    ) -> int:

        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        encoded = urlencode({'text': text, 'reply_markup': reply_markup})
        async with self.session.get(
                f'https://api.telegram.org/bot{self.token}/sendMessage?chat_id={self.database.chat_id}&{encoded}&'
                f'reply_to_message_id={reply_to_message_id}&parse_mode={parse_mode}&'
                f'disable_web_page_preview={disable_web_page_preview}'
        ) as response:
            response = await response.json()
            if response['ok']:
                return response['result']['message_id']
            return 0

    @fix
    async def delete_message(self, message_id: int, /) -> None:
        async with self.session.get(
                f'https://api.telegram.org/bot{self.token}/deleteMessage?chat_id={self.database.chat_id}&'
                f'message_id={message_id}'
        ):
            pass

    @sync_to_async
    def save(self):
        self.database.save()
