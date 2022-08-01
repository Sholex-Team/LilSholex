from httpcore import stream
from LilSholex.decorators import sync_fix
import json
from persianmeme.models import User as PersianMemeUser
from typing import Union
from abc import ABC, abstractmethod
from requests import Session
from django.conf import settings
from .exceptions import TooManyRequests


class Base(ABC):
    database: Union[PersianMemeUser]
    _BASE_URL: str

    def __init__(
            self,
            token: str,
            chat_id: Union[int, None],
            instance: Union[PersianMemeUser, None],
            session: Session
    ):
        self.token = token
        self.chat_id = chat_id
        self.session = session
        self._instance = instance
        if not self.chat_id:
            assert self._instance, 'Instance must be passed when chat id isn\'t !'
            self.database = self._instance
        else:
            self.database = self.get_user()
        self._BASE_PARAM = {'chat_id': self.database.chat_id}

    @abstractmethod
    def get_user(self) -> PersianMemeUser:
        pass

    @sync_fix
    def send_message(
            self,
            text: str,
            reply_markup: dict = str(),
            reply_to_message_id: int = str(),
            parse_mode: str = None,
            disable_web_page_preview: bool = True,
    ) -> int:
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        with self.session.get(
            f'{self._BASE_URL}sendMessage',
            params={
                **self._BASE_PARAM,
                'text': text,
                'reply_markup': reply_markup,
                'reply_to_message_id': reply_to_message_id,
                'parse_mode': parse_mode if parse_mode else str(),
                'disable_web_page_preview': str(disable_web_page_preview)
            },
            timeout=settings.REQUESTS_TIMEOUT
        ) as response:
            if response.status_code == 200:
                if (result := response.json())['ok']:
                    return result['result']['message_id']
            elif response.status_code != 429:
                return 0
            raise TooManyRequests(response.json()['parameters']['retry_after'])
    
    def send_voice(
            self,
            file_path,
            caption = ""
    ) -> int:
        with self.session.get(
            f'{self._BASE_URL}sendVoice',
            params={
                **self._BASE_PARAM,
                'caption': caption
            },
            files={'voice': open(file_path, 'rb')},
            timeout=settings.REQUESTS_TIMEOUT
        ) as response:
            if response.status_code == 200:
                if (result := response.json())['ok']:
                    return result['result']
            elif response.status_code != 429:
                return 0
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    @sync_fix
    def get_file_path(
            self,
            file_id: str
    ) -> str:
        with self.session.get(
            f'{self._BASE_URL}getFile',
            params={
                **self._BASE_PARAM,
                'file_id': file_id
            },
            timeout=settings.REQUESTS_TIMEOUT
        ) as response:
            if response.status_code == 200:
                if (result := response.json())['ok']:
                    return result['result']['file_path']
            elif response.status_code != 429:
                return 0
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    @sync_fix
    def download_file(
            self,
            file_path: str,
    ) -> str:
        file_name = 'downloads/' + self.database.last_meme.file_id + '.ogg'
        with self.session.get(
            self._BASE_URL.replace('bot', 'file/') + file_path,
            timeout=settings.REQUESTS_TIMEOUT
        ) as response:
            if response.status_code == 200:
                with open(file_name, 'wb') as f:
                    f.write(response.content)
                return file_name
            elif response.status_code != 429:
                return 0
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    @sync_fix
    def delete_message(self, message_id: int) -> None:
        with self.session.get(
            f'{self._BASE_URL}deleteMessage',
            params={**self._BASE_PARAM, 'message_id': message_id},
            timeout=settings.REQUESTS_TIMEOUT
        ) as response:
            if response.status_code != 429:
                return
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    @sync_fix
    def edit_message_text(self, message_id: int, text: str, inline_keyboard: dict = str()):
        if inline_keyboard:
            inline_keyboard = json.dumps(inline_keyboard)
        with self.session.get(
            f'{self._BASE_URL}editMessageText',
            params={**self._BASE_PARAM, 'message_id': message_id, 'text': text, 'reply_markup': inline_keyboard},
            timeout=settings.REQUESTS_TIMEOUT
        ) as response:
            if response.status_code != 429:
                return
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    @sync_fix
    def send_animation(
            self,
            animation: str,
            caption: str = str(),
            reply_markup: dict = str(),
            reply_to_message_id: int = str(),
            parse_mode: str = str()
    ):
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        with self.session.get(f'{self._BASE_URL}sendAnimation', params={
            **self._BASE_PARAM,
            'animation': animation,
            'caption': caption,
            'reply_markup': reply_markup,
            'reply_to_message_id': reply_to_message_id,
            'parse_mode': parse_mode
        }, timeout=settings.REQUESTS_TIMEOUT) as response:
            if response.status_code != 429:
                return
            raise TooManyRequests(response.json()['parameters']['retry_after'])

    @abstractmethod
    def go_back(self):
        pass

    @abstractmethod
    def translate(self, key: str, *formatting_args):
        pass
