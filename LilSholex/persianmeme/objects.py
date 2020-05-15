from persianmeme import models
import faster_than_requests as fast_req
from urllib.parse import urlencode
import json
from django.conf import settings
import time
from groupguard.decorators import fix


class User:
    def __init__(self, chat_id: int = None, instance: models.User = None):
        if instance:
            self.database = instance
        else:
            user, created = models.User.objects.get_or_create(chat_id=chat_id, defaults={'last_date': time.time()})
            self.database = user

    @fix
    def send_message(self, text: str, reply_markup: dict = '', /, reply_to_message_id: int = '', parse_mode: str = ''):
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        encoded = urlencode({'text': text, 'reply_markup': reply_markup})
        fast_req.get(f'https://api.telegram.org/bot{settings.MEME}/sendMessage?chat_id={self.database.chat_id}&'
                     f'{encoded}&reply_to_message_id={reply_to_message_id}&parse_mode={parse_mode}')

    @fix
    def send_voice(self, file_id: str, caption: str, reply_markup: dict = '', reply_to_message_id: int = ''):
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        encoded = urlencode({'caption': caption, 'reply_markup': reply_markup})
        fast_req.get(f'https://api.telegram.org/bot{settings.MEME}/sendVoice?chat_id={self.database.chat_id}&'
                     f'voice={file_id}&{encoded}&reply_to_message_id={reply_to_message_id}')

    def delete_message(self, message_id: int):
        fast_req.get(f'https://api.telegram.org/bot{settings.MEME}/deleteMessage?chat_id={self.database.chat_id}&'
                     f'message_id={message_id}')

    def forward_message(self, from_chat_id: int, message_id: int):
        fast_req.get(f'https://api.telegram.org/bot{settings.MEME}/forwardMessage?chat_id={self.database.chat_id}'
                     f'&from_chat_id={from_chat_id}&message_id={message_id}')

    def send_ad(self):
        for mass in models.Ad.objects.exclude(seen=self.database):
            self.forward_message(mass.chat_id, mass.message_id)
            mass.seen.add(self.database)
            mass.save()

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

    @fix
    def get_chat(self):
        return json.loads(fast_req.get(
            f'https://api.telegram.org/bot{settings.MEME}/getChat?chat_id={self.database.chat_id}'
        )['body']).get('result', {})

    def set_username(self):
        if self.get_chat().get('username'):
            self.database.username = '@' + self.get_chat()['username']
