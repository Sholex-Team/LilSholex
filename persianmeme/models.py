import json
from urllib.parse import urlencode
import requests
from django.conf import settings
from django.db import models
from LilSholex.decorators import async_fix
from .keyboards import voice as voice_keyboard
from aiohttp import ClientSession
from asgiref.sync import sync_to_async
from uuid import uuid4
from . import translations


class User(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'a', 'Active'
        BANNED = 'b', 'Banned'
        FULL_BANNED = 'f', 'Full Banned'

    class Rank(models.TextChoices):
        OWNER = 'o', 'Owner'
        USER = 'u', 'User'
        ADMIN = 'a', 'Admin'
        KHIAR = 'k', 'Khiar'

    class VoiceOrder(models.TextChoices):
        votes = 'votes', 'Votes (Low to High)'
        voice_id = 'voice_id', 'Voice ID (Old to New)'
        high_votes = '-votes', 'Votes (High to Low)'
        new_voice_id = '-voice_id', 'Voice ID (New to Old)'

    class MenuMode(models.TextChoices):
        ADMIN = 'a', 'Admin'
        USER = 'u', 'User'

    user_id = models.AutoField(verbose_name='User ID', primary_key=True, unique=True)
    chat_id = models.BigIntegerField(verbose_name='User Chat ID', unique=True)
    menu = models.IntegerField(verbose_name='Current Menu', default=1)
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Current Status'
    )
    rank = models.CharField(max_length=1, choices=Rank.choices, default=Rank.USER, verbose_name='User Rank')
    sent_message = models.BooleanField(verbose_name='Sent Message', default=False)
    username = models.CharField(max_length=35, verbose_name='Username', null=True, blank=True)
    temp_voice_name = models.CharField(max_length=50, null=True)
    temp_user_id = models.BigIntegerField(null=True)
    last_usage_date = models.DateTimeField(auto_now=True, verbose_name='Last Usage Date')
    vote = models.BooleanField(verbose_name='Vote System', default=False)
    date = models.DateTimeField(verbose_name='Register Date', auto_now_add=True)
    voice_order = models.CharField(max_length=9, choices=VoiceOrder.choices, default=VoiceOrder.new_voice_id)
    private_voices = models.ManyToManyField('Voice', 'private_voices', verbose_name='Private Voices')
    favorite_voices = models.ManyToManyField('Voice', 'favorite_voices', verbose_name='Favorite Voices', blank=True)
    back_menu = models.CharField(max_length=50, null=True, blank=True)
    started = models.BooleanField('Started', default=False)
    last_start = models.DateTimeField(null=True, blank=True, verbose_name='Last Start')
    last_broadcast = models.ForeignKey(
        'Broadcast', models.SET_NULL, 'user_broadcast', null=True, blank=True, verbose_name='Last Broadcast'
    )
    playlists = models.ManyToManyField('Playlist', 'user_playlist', verbose_name='Playlists', blank=True)
    current_playlist = models.ForeignKey(
        'Playlist',
        models.SET_NULL,
        'user_current_playlist',
        blank=True, null=True,
        verbose_name='Current Playlist',
        default=None
    )
    current_voice = models.ForeignKey(
        'Voice',
        models.SET_NULL,
        'user_voice',
        blank=True,
        null=True,
        verbose_name='Current Voice',
        default=None
    )
    current_ad = models.ForeignKey('Ad', models.SET_NULL, 'user_ad', null=True, blank=True, verbose_name='Current Ad')
    menu_mode = models.CharField(
        max_length=1, verbose_name='Menu Mode', choices=MenuMode.choices, default=MenuMode.USER
    )

    class Meta:
        db_table = 'persianmeme_users'
        ordering = ['user_id']

    def __str__(self):
        return f'{self.chat_id}:{self.rank}'


class Voice(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'a', 'Active'
        PENDING = 'p', 'Pending'
        SEMI_ACTIVE = 's', 'Semi Active'

    class Type(models.TextChoices):
        NORMAL = 'n', 'Normal'
        PRIVATE = 'p', 'Private'

    @sync_to_async
    def ban_sender(self):
        self.sender.status = self.sender.Status.BANNED
        self.sender.save()
        self.deny()

    def delete(self, *args, **kwargs):
        if not kwargs.get('dont_send'):
            from .functions import send_message
            admin = f' by {kwargs.pop("admin")}' if kwargs.get('admin') else ''
            send_message(
                settings.MEME_LOGS,
                translations.admin_messages['deleted_by_admins'].format(admin, self.name, self.file_id)
            )
            send_message(
                self.sender.chat_id,
                translations.user_messages['deleted_by_admins'].format(self.name)
            )
        else:
            del kwargs['dont_send']
        super().delete(*args, **kwargs)

    voice_id = models.AutoField(verbose_name='Voice ID', unique=True, primary_key=True)
    message_id = models.BigIntegerField(verbose_name='Message ID', null=True, blank=True)
    file_id = models.CharField(max_length=200, verbose_name='Voice File ID')
    file_unique_id = models.CharField(max_length=100, verbose_name='Voice Unique ID')
    name = models.CharField(max_length=200, verbose_name='Voice Name')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Voice Sender', related_name='senders')
    voters = models.ManyToManyField(User, verbose_name='Voters', related_name='voters', blank=True)
    votes = models.IntegerField(default=0, verbose_name='Up Votes')
    status = models.CharField(max_length=1, choices=Status.choices, verbose_name='Voice Status')
    date = models.DateTimeField(auto_now_add=True, verbose_name='Register Date')
    last_check = models.DateTimeField(auto_now=True, verbose_name='Last Check')
    voice_type = models.CharField(max_length=1, choices=Type.choices, default=Type.NORMAL, verbose_name='Voice Type')
    accept_vote = models.ManyToManyField(User, 'accept_vote_users', blank=True, verbose_name='Accept Votes')
    deny_vote = models.ManyToManyField(User, 'deny_vote_users', blank=True, verbose_name='Deny Votes')

    class Meta:
        db_table = 'persianmeme_voices'
        ordering = ['-voice_id']

    def __str__(self):
        return f'{self.name}:{self.file_id}'

    @sync_to_async
    def async_accept(self):
        self.status = self.Status.SEMI_ACTIVE
        self.save()
        self.accept_vote.clear()
        self.deny_vote.clear()
        return self.sender

    @sync_to_async
    def async_deny(self):
        sender = self.sender
        self.delete(dont_send=True)
        return sender

    def accept(self):
        from .functions import send_message
        self.status = self.Status.SEMI_ACTIVE
        self.save()
        self.accept_vote.clear()
        self.deny_vote.clear()
        send_message(self.sender.chat_id, translations.user_messages['voice_accepted'])
        for admin in User.objects.filter(rank=User.Rank.ADMIN):
            send_message(admin.chat_id, translations.admin_messages['voice_accepted'])

    def deny(self):
        from .functions import send_message
        send_message(self.sender.chat_id, translations.user_messages['voice_denied'])
        self.delete(dont_send=True)

    @sync_to_async
    def get_voters(self):
        return tuple(self.voters.all())

    def edit_vote_count(self):
        while True:
            try:
                if requests.get(f'https://api.telegram.org/bot{settings.MEME}/editMessageReplyMarkup', params={
                    'chat_id': settings.MEME_CHANNEL,
                    'message_id': self.message_id,
                    'reply_markup': json.dumps(voice_keyboard(self.accept_vote.count(), self.deny_vote.count()))
                }) == 429:
                    raise requests.RequestException()
            except requests.RequestException:
                continue
            break

    @async_fix
    async def send_voice(self, session: ClientSession) -> int:
        encoded = urlencode({
            'caption': f'<b>Voice Name</b>: {self.name}',
            'parse_mode': 'Html',
            'reply_markup': json.dumps(voice_keyboard())
        })
        async with session.get(
                f'https://api.telegram.org/bot{settings.MEME}/sendVoice?chat_id={settings.MEME_CHANNEL}&'
                f'voice={self.file_id}&{encoded}'
        ) as response:
            response = await response.json()
            if response['ok']:
                return response['result']['message_id']
        return 0


class Ad(models.Model):
    ad_id = models.AutoField(primary_key=True, verbose_name='Mass ID')
    chat_id = models.BigIntegerField(verbose_name='Chat ID')
    message_id = models.IntegerField(verbose_name='Message ID')
    seen = models.ManyToManyField(User, 'mass_seens', verbose_name='Seen By', blank=True)

    class Meta:
        db_table = 'persianmeme_ads'
        ordering = ['ad_id']

    def __str__(self):
        return str(self.ad_id)


class Delete(models.Model):
    delete_id = models.AutoField(primary_key=True, verbose_name='Delete ID')
    voice = models.ForeignKey(Voice, models.CASCADE, 'deletes_voice', verbose_name='Voice')
    user = models.ForeignKey(User, models.CASCADE, 'deletes_user', verbose_name='User')

    class Meta:
        db_table = 'persianmeme_deletes'
        ordering = ['delete_id']

    def __str__(self):
        return f'{self.delete_id} : {self.voice.voice_id}'

    @sync_to_async
    def get_voice(self):
        return self.voice

    @sync_to_async
    def get_user(self):
        return self.user


class Broadcast(models.Model):
    message_id = models.IntegerField('Message ID')
    sender = models.ForeignKey(User, models.CASCADE, 'broadcast_user', verbose_name='Sender Admin')
    sent = models.BooleanField('Sent', default=False)

    @property
    @sync_to_async
    def get_sender(self):
        return self.sender

    def __str__(self):
        return f'{self.id}:{self.message_id}'

    class Meta:
        db_table = 'persianmeme_broadcasts'
        ordering = ['-id']


class Playlist(models.Model):
    invite_link = models.UUIDField('Invite ID', default=uuid4)
    name = models.CharField(max_length=60, verbose_name='Name')
    voices = models.ManyToManyField(Voice, 'playlist_voice', verbose_name='Voices')
    creator = models.ForeignKey(User, models.CASCADE, verbose_name='Creator')
    date = models.DateTimeField('Creation Date', auto_now_add=True)

    def get_link(self):
        return f'https://t.me/Persian_Meme_Bot?start={self.invite_link}'

    class Meta:
        db_table = 'persianmeme_playlists'
        ordering = ['-date']

    def __str__(self):
        return f'{self.name}:{self.creator.chat_id}'


PUBLIC_STATUS = (Voice.Status.ACTIVE, Voice.Status.SEMI_ACTIVE)
BOT_ADMINS = (User.Rank.ADMIN, User.Rank.OWNER)
