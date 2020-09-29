from . import models
import json
from django.conf import settings
import time
from LilSholex.decorators import fix
from LilSholex.classes import Base
from . import steps
import requests


class User(Base):
    BASE_URL = f'https://api.telegram.org/bot{settings.MEME}/'
    
    def get_user(self):
        return models.User.objects.get_or_create(chat_id=self.chat_id, defaults={'last_date': time.time()})

    def __init__(self, chat_id: int = None, instance: models.User = None):
        super().__init__(settings.MEME, chat_id, instance)

    @fix
    async def send_voice(self, file_id: str, caption: str, reply_markup: dict = '', reply_to_message_id: int = ''):
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        encoded = {'caption': caption, 'reply_markup': reply_markup}
        requests.get(
            f'{self.BASE_URL}sendVoice',
            params={**self.BASE_PARAM, **encoded, 'voice': file_id, 'reply_to_message_id': reply_to_message_id}
        )

    def delete_message(self, message_id: int):
        requests.get(f'{self.BASE_URL}deleteMessage', params={**self.BASE_PARAM, 'message_id': message_id})

    def forward_message(self, from_chat_id: int, message_id: int):
        requests.get(
            f'{self.BASE_URL}forwardMessage',
            params={**self.BASE_PARAM, 'from_chat_id': from_chat_id, 'message_id': message_id}
        )

    def __get_ads(self):
        return models.Ad.objects.exclude(seen=self.database)

    def __save_ad(self, ad: models.Ad):
        ad.seen.add(self.database)
        ad.save()

    def send_ad(self):
        for ad in self.__get_ads():
            self.forward_message(ad.chat_id, ad.message_id)
            self.__save_ad(ad)

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

    def delete_request(self, voice: models.Voice):
        models.Delete.objects.create(voice=voice, user=self.database)

    @fix
    def get_chat(self):
        response = requests.get(f'{self.BASE_URL}getChat', self.BASE_PARAM).json()
        return response.get('result', {})

    def set_username(self):
        username = self.get_chat().get('username')
        if username:
            self.database.username = '@' + username

    def like_voice(self, target_voice: models.Voice):
        if self.database in target_voice.accept_vote.all():
            return False
        else:
            if self.database in target_voice.deny_vote.all():
                target_voice.deny_vote.remove(self.database)
            target_voice.accept_vote.add(self.database)
        return True

    def dislike_voice(self, target_voice: models.Voice):
        if self.database in target_voice.deny_vote.all():
            return False
        else:
            if self.database in target_voice.accept_vote.all():
                target_voice.accept_vote.remove(self.database)
            target_voice.deny_vote.add(self.database)
        return True

    def add_voter(self, voice: models.Voice):
        voice.voters.add(self.database)

    def remove_voter(self, voice: models.Voice):
        voice.voters.remove(self.database)

    def private_user_count(self):
        return self.database.private_voices.count()

    def delete_private_voice(self, voice: models.Voice):
        if voice in self.database.private_voices.all():
            voice.delete()
            return True

    def create_private_voice(self, message: dict):
        self.database.private_voices.create(
            file_id=message['voice']['file_id'],
            file_unique_id=message['voice']['file_unique_id'],
            status='a',
            voice_type='p',
            sender=self.database,
            name=self.database.temp_voice_name
        )

    def add_favorite_voice(self, voice: models.Voice):
        if voice not in self.database.favorite_voices.all():
            self.database.favorite_voices.add(voice)
            return True

    def delete_favorite_voice(self, voice: models.Voice):
        self.database.favorite_voices.remove(voice)

    def count_favorite_voices(self):
        return self.database.favorite_voices.count()

    def remove_voice(self, file_unique_id: str):
        target_voices = models.Voice.objects.filter(
            file_unique_id=file_unique_id,
            status='a',
            sender=self.database,
            voice_type='n'
        )
        if target_voices.exists():
            target_voices.delete()
            return True
    
    def send_help(self):
        requests.get(
            f'{self.BASE_URL}sendVideo',
            params={**self.BASE_PARAM, 'video': settings.MEME_ANIM, 'caption': 'گیف راهنما 👆'}
        )

    def go_back(self):
        try:
            if self.database.rank != self.database.Rank.user:
                step = steps.admin_steps[self.database.back_menu]
            else:
                step = steps.user_steps[self.database.back_menu]
        except KeyError:
            if self.database.rank != self.database.Rank.user:
                step = steps.admin_steps['main']
            else:
                step = steps.user_steps['main']
        self.database.menu = step['menu']
        self.database.back_menu = step.get('before')
        self.send_message(step['message'], step.get('keyboard', ''))
        self.save()
