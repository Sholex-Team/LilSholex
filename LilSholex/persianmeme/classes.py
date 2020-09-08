from . import models
from urllib.parse import urlencode
import json
from django.conf import settings
import time
from LilSholex.decorators import fix
from LilSholex.classes import Base
from aiohttp import ClientSession
from asgiref.sync import sync_to_async


class User(Base):
    @sync_to_async
    def get_user(self):
        return models.User.objects.get_or_create(chat_id=self.chat_id, defaults={'last_date': time.time()})

    def __init__(self, session: ClientSession, chat_id: int = None, instance: models.User = None):
        super().__init__(settings.MEME, chat_id, instance, session)

    @fix
    async def send_voice(self, file_id: str, caption: str, reply_markup: dict = '', reply_to_message_id: int = ''):
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        encoded = urlencode({'caption': caption, 'reply_markup': reply_markup})
        async with self.session.get(
            f'https://api.telegram.org/bot{settings.MEME}/sendVoice?chat_id={self.database.chat_id}&'
            f'voice={file_id}&{encoded}&reply_to_message_id={reply_to_message_id}'
        ):
            pass

    async def delete_message(self, message_id: int):
        async with self.session.get(
            f'https://api.telegram.org/bot{settings.MEME}/deleteMessage?chat_id={self.database.chat_id}&'
            f'message_id={message_id}'
        ):
            pass

    async def forward_message(self, from_chat_id: int, message_id: int):
        async with self.session.get(
            f'https://api.telegram.org/bot{settings.MEME}/forwardMessage?chat_id={self.database.chat_id}'
            f'&from_chat_id={from_chat_id}&message_id={message_id}'
        ):
            pass

    @sync_to_async
    def __get_ads(self):
        return list(models.Ad.objects.exclude(seen=self.database))

    @sync_to_async
    def __save_ad(self, ad: models.Ad):
        ad.seen.add(self.database)
        ad.save()

    async def send_ad(self):
        for ad in await self.__get_ads():
            await self.forward_message(ad.chat_id, ad.message_id)
            await self.__save_ad(ad)

    @sync_to_async
    def get_voices(self, query, offset):
        if self.database.vote:
            results = [{'type': 'voice', 'id': voice.voice_id, 'voice_file_id': voice.file_id, 'title': voice.name,
                        'reply_markup': {
                            'inline_keyboard': [[
                                {'text': '👍', 'callback_data': f'up:{voice.voice_id}'},
                                {'text': '👎', 'callback_data': f'down:{voice.voice_id}'}
                            ]]
                        }} for voice in self.database.private_voices.all().order_by(self.database.voice_order).filter(
                name__icontains=query
            )]
            results.extend([{'type': 'voice', 'id': voice.voice_id, 'voice_file_id': voice.file_id, 'title': voice.name,
                             'reply_markup': {'inline_keyboard': [[
                                 {'text': '👍', 'callback_data': f'up:{voice.voice_id}'},
                                 {'text': '👎', 'callback_data': f'down:{voice.voice_id}'}
                             ]]}} for voice in self.database.favorite_voices.all().order_by(
                self.database.voice_order
            ).filter(name__icontains=query, status='a')])
            results.extend([{'type': 'voice', 'id': voice.voice_id, 'voice_file_id': voice.file_id, 'title': voice.name,
                             'reply_markup': {'inline_keyboard': [
                                 [{'text': '👍', 'callback_data': f'up:{voice.voice_id}'},
                                  {'text': '👎', 'callback_data': f'down:{voice.voice_id}'}]]}} for voice in
                            models.Voice.objects.order_by(self.database.voice_order).filter(
                                name__icontains=query, status='a', voice_type='n'
                            )])
        else:
            results = [
                {'type': 'voice', 'id': voice.voice_id, 'voice_file_id': voice.file_id, 'title': voice.name
                 } for voice in self.database.private_voices.all().order_by(self.database.voice_order).filter(
                    name__icontains=query, status='a', voice_type='p'
                )]
            results.extend([{
                'type': 'voice', 'id': voice.voice_id, 'voice_file_id': voice.file_id, 'title': voice.name
            } for voice in self.database.favorite_voices.all().order_by(self.database.voice_order).filter(
                name__icontains=query, status='a'
            )])
            results.extend([
                {
                    'type': 'voice', 'id': voice.voice_id, 'voice_file_id': voice.file_id, 'title': voice.name
                } for voice in models.Voice.objects.order_by(self.database.voice_order).filter(
                    name__icontains=query, status='a', voice_type='n'
                )
            ])
        if offset == '':
            return results[:50], 1
        else:
            offset = int(offset)
            return results[offset * 50:offset * 50 + 50], offset + 1

    @sync_to_async
    def delete_request(self, voice: models.Voice):
        models.Delete.objects.create(voice=voice, user=self.database)

    @fix
    async def get_chat(self):
        async with self.session.get(
            f'https://api.telegram.org/bot{settings.MEME}/getChat?chat_id={self.database.chat_id}'
        ) as response:
            response = await response.json()
            return response.get('result', {})

    async def set_username(self):
        if username := (await self.get_chat()).get('username'):
            self.database.username = '@' + username

    @sync_to_async
    def like_voice(self, target_voice: models.Voice):
        if self.database in target_voice.accept_vote.all():
            return False
        else:
            if self.database in target_voice.deny_vote.all():
                target_voice.deny_vote.remove(self.database)
            target_voice.accept_vote.add(self.database)
        return True

    @sync_to_async
    def dislike_voice(self, target_voice: models.Voice):
        if self.database in target_voice.deny_vote.all():
            return False
        else:
            if self.database in target_voice.accept_vote.all():
                target_voice.accept_vote.remove(self.database)
            target_voice.deny_vote.add(self.database)
        return True

    @sync_to_async
    def add_voter(self, voice: models.Voice):
        voice.voters.add(self.database)

    @sync_to_async
    def remove_voter(self, voice: models.Voice):
        voice.voters.remove(self.database)

    @sync_to_async
    def private_user_count(self):
        return self.database.private_voices.count()

    @sync_to_async
    def delete_private_voice(self, voice: models.Voice):
        if voice in self.database.private_voices.all():
            voice.delete()
            return True

    @sync_to_async
    def create_private_voice(self, message: dict):
        self.database.private_voices.create(
            file_id=message['voice']['file_id'],
            file_unique_id=message['voice']['file_unique_id'],
            status='a',
            voice_type='p',
            sender=self.database,
            name=self.database.temp_voice_name
        )

    @sync_to_async
    def add_favorite_voice(self, voice: models.Voice):
        if voice not in self.database.favorite_voices.all():
            self.database.favorite_voices.add(voice)
            return True

    @sync_to_async
    def delete_favorite_voice(self, voice: models.Voice):
        self.database.favorite_voices.remove(voice)

    @sync_to_async
    def count_favorite_voices(self):
        return self.database.favorite_voices.count()

    @sync_to_async
    def remove_voice(self, file_unique_id: str):
        if (target_voices := models.Voice.objects.filter(
            file_unique_id=file_unique_id,
            status='a',
            sender=self.database,
            voice_type='n'
        )).exists():
            target_voices.delete()
            return True
