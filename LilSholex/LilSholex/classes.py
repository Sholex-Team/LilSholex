from LilSholex.decorators import fix
import json
from persianmeme.models import User as PersianMemeUser
from typing import Union, Tuple
import requests
from abc import ABC, abstractmethod


class Base(ABC):
    database: PersianMemeUser
    BASE_URL: str

    def __init__(
            self,
            token: str,
            chat_id: Union[int, None],
            instance: Union[PersianMemeUser, None]
    ):
        self.token = token
        self.chat_id = chat_id
        self.__instance = instance
        if not self.chat_id:
            assert self.__instance, 'Instance must be passed when chat id isn\'t !'
            self.database = self.__instance
        else:
            self.database, created = self.get_user()
        self.BASE_PARAM = {'chat_id': self.database.chat_id}

    @abstractmethod
    def get_user(self) -> Tuple[PersianMemeUser, bool]:
        pass

    @fix
    def send_message(
            self,
            text: str,
            reply_markup: dict = '',
            reply_to_message_id: int = '',
            parse_mode: str = None,
            disable_web_page_preview: bool = True,
    ) -> int:

        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        encoded = {'text': text, 'reply_markup': reply_markup}
        response = requests.get(
            f'{self.BASE_URL}sendMessage',
            params={
                **self.BASE_PARAM,
                **encoded,
                'reply_to_message_id': reply_to_message_id,
                'parse_mode': parse_mode,
                'disable_web_page_preview': disable_web_page_preview
            }
        ).json()
        if response['ok']:
            return response['result']['message_id']
        return 0

    @fix
    def delete_message(self, message_id: int) -> None:
        requests.get(
            f'{self.BASE_URL}deleteMessage',
            params={**self.BASE_PARAM, 'message_id': message_id}
        )

    def save(self):
        self.database.save()

    @abstractmethod
    def go_back(self):
        pass
