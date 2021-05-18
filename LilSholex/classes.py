from LilSholex.decorators import async_fix
import json
from persianmeme.models import User as PersianMemeUser
from typing import Union, Tuple
from aiohttp import ClientSession
from abc import ABC, abstractmethod
from asgiref.sync import sync_to_async


class Base(ABC):
    database: Union[PersianMemeUser]
    _BASE_URL: str

    def __init__(
            self,
            token: str,
            chat_id: Union[int, None],
            instance: Union[PersianMemeUser, None],
            session: ClientSession
    ):
        self.token = token
        self.chat_id = chat_id
        self._session = session
        self._instance = instance

    def __await__(self):
        if not self.chat_id:
            assert self._instance, 'Instance must be passed when chat id isn\'t !'
            self.database = self._instance
        else:
            self.database = yield from self.get_user().__await__()
        self._BASE_PARAM = {'chat_id': self.database.chat_id}
        return self

    @abstractmethod
    def get_user(self) -> Tuple[PersianMemeUser, bool]:
        pass

    @async_fix
    async def send_message(
            self,
            text: str,
            reply_markup: dict = str(),
            reply_to_message_id: int = str(),
            parse_mode: str = None,
            disable_web_page_preview: bool = True,
    ) -> int:
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        async with self._session.get(
            f'{self._BASE_URL}sendMessage',
            params={
                **self._BASE_PARAM,
                'text': text,
                'reply_markup': reply_markup,
                'reply_to_message_id': reply_to_message_id,
                'parse_mode': parse_mode if parse_mode else str(),
                'disable_web_page_preview': str(disable_web_page_preview)
            }
        ) as response:
            response = await response.json()
            if response['ok']:
                return response['result']['message_id']
            return 0

    @async_fix
    async def delete_message(self, message_id: int) -> None:
        async with self._session.get(
            f'{self._BASE_URL}deleteMessage',
            params={**self._BASE_PARAM, 'message_id': message_id}
        ) as _:
            return

    @async_fix
    async def edit_message_text(self, message_id: int, text: str, inline_keyboard: dict = str()):
        if inline_keyboard:
            inline_keyboard = json.dumps(inline_keyboard)
        async with self._session.get(
            f'{self._BASE_URL}editMessageText',
            params={**self._BASE_PARAM, 'message_id': message_id, 'text': text, 'reply_markup': inline_keyboard}
        ) as _:
            return

    @async_fix
    async def send_animation(
            self,
            animation: str,
            caption: str = str(),
            reply_markup: dict = str(),
            reply_to_message_id: int = str(),
            parse_mode: str = str()
    ):
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        async with self._session.get(f'{self._BASE_URL}sendAnimation', params={
            **self._BASE_PARAM,
            'animation': animation,
            'caption': caption,
            'reply_markup': reply_markup,
            'reply_to_message_id': reply_to_message_id,
            'parse_mode': parse_mode
        }):
            return

    @sync_to_async
    def save(self):
        self.database.save()

    @abstractmethod
    async def go_back(self):
        pass

    @abstractmethod
    def translate(self, key: str, *formatting_args):
        pass
