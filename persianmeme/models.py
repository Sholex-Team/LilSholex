import json
import requests
from django.conf import settings
from django.db import models
from LilSholex.decorators import sync_fix
from .keyboards import voice_recovery
from asgiref.sync import sync_to_async
from uuid import uuid4
from . import translations
from LilSholex.exceptions import TooManyRequests


class VoiceTag(models.Model):
    tag = models.CharField(max_length=32, verbose_name='Tag Content', primary_key=True)

    class Meta:
        ordering = ['tag']
        db_table = 'persianmeme_voice_tags'


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
        voice_id = 'id', 'Voice ID (Old to New)'
        high_votes = '-votes', 'Votes (High to Low)'
        new_voice_id = '-id', 'Voice ID (New to Old)'
        high_usage = '-usage_count', 'Usage Count (High to Low)'
        low_usage = 'usage_count', 'Usage Count (Low to High)'

    class MenuMode(models.TextChoices):
        ADMIN = 'a', 'Admin'
        USER = 'u', 'User'

    class Menu(models.IntegerChoices):
        ADMIN_MAIN = 1, 'Admin Main Menu'
        ADMIN_VOICE_NAME = 2, 'Admin Voice Name',
        ADMIN_NEW_VOICE = 3, 'Admin New Voice'
        ADMIN_DELETE_VOICE = 4, 'Admin Delete Voice'
        ADMIN_BAN_USER = 5, 'Admin Ban User'
        ADMIN_UNBAN_USER = 6, 'Admin Unban User'
        ADMIN_FULL_BAN_USER = 7, 'Admin Full Ban User'
        ADMIN_MESSAGE_USER_ID = 8, 'Admin Message User ID'
        ADMIN_MESSAGE_USER = 9, 'Admin Message User'
        ADMIN_ADD_AD = 10, 'Admin Add Ad'
        ADMIN_DELETE_AD = 11, 'Admin Delete Ad'
        ADMIN_GET_USER = 12, 'Admin Get User'
        ADMIN_BROADCAST = 13, 'Admin Broadcast'
        ADMIN_EDIT_AD_ID = 14, 'Admin Edit Ad ID'
        ADMIN_EDIT_AD = 15, 'Admin Edit Ad'
        ADMIN_BAN_VOTE = 16, 'Admin Ban Vote'
        ADMIN_DENY_VOICE = 17, 'Admin Deny Voice'
        ADMIN_ACCEPT_VOICE = 18, 'Admin Accept Voice'
        ADMIN_GET_VOICE = 40, 'Admin Get Voice'
        ADMIN_VOICE_TAGS = 42, 'Admin Voice Tags',
        ADMIN_SEND_EDIT_VOICE = 44, 'Admin Send Edit Voice',
        ADMIN_EDIT_VOICE = 45, 'Admin Edit Voice',
        ADMIN_EDIT_VOICE_NAME = 46, 'Admin Edit Voice Name',
        ADMIN_EDIT_VOICE_TAGS = 47, 'Admin Edit Voice Tags',
        ADMIN_FILE_ID = 48, 'Admin File ID'
        ADMIN_VOICE_REVIEW = 54, 'Admin Voice Review'
        USER_MAIN = 19, 'User Main'
        USER_CONTACT_ADMIN = 20, 'User Contact Admin'
        USER_SUGGEST_VOICE_NAME = 21, 'User Suggest Voice Name'
        USER_SUGGEST_VOICE = 22, 'User Suggest Voice'
        USER_RANKING = 24, 'User Ranking'
        USER_SORTING = 25, 'User Sorting'
        USER_DELETE_REQUEST = 26, 'User Delete Request'
        USER_PRIVATE_VOICES = 27, 'User Private Voices'
        USER_PRIVATE_VOICE_NAME = 28, 'User Private Voice Name'
        USER_MANAGE_PRIVATE_VOICE = 29, 'User Manage Private Voice'
        USER_PRIVATE_VOICE = 30, 'User Private Voice'
        USER_FAVORITE_VOICES = 31, 'User Favorite Voices'
        USER_FAVORITE_VOICE = 32, 'User Favorite Voice'
        USER_MANAGE_FAVORITE_VOICE = 33, 'User Manage Favorite Voice'
        USER_PLAYLISTS = 35, 'User Playlists'
        USER_CREATE_PLAYLIST = 36, 'User Create Playlist'
        USER_MANAGE_PLAYLIST = 37, 'User Manage Playlist'
        USER_ADD_VOICE_PLAYLIST = 38, 'User Add Voice To Playlist'
        USER_MANAGE_PLAYLIST_VOICE = 39, 'User Manager Playlist Voice'
        USER_SUGGEST_VOICE_TAGS = 41, 'User Suggest Voice Tags'
        USER_PRIVATE_VOICE_TAGS = 43, 'User Private Voice Tags'
        USER_HELP = 49, 'User Help'
        USER_SETTINGS = 50, 'User Settings'
        USER_RECENT_VOICES = 51, 'User Recent Voices'
        USER_SUGGESTIONS = 52, 'User Suggestions'
        USER_MANAGE_SUGGESTION = 53, 'User Manage Suggestion'

    user_id = models.AutoField(verbose_name='User ID', primary_key=True, unique=True)
    chat_id = models.BigIntegerField(verbose_name='Chat ID', unique=True)
    menu = models.PositiveSmallIntegerField(verbose_name='Current Menu', choices=Menu.choices, default=Menu.USER_MAIN)
    status = models.CharField(max_length=1, choices=Status.choices, default=Status.ACTIVE)
    rank = models.CharField(max_length=1, choices=Rank.choices, default=Rank.USER)
    username = models.CharField(max_length=35, null=True, blank=True)
    temp_voice_name = models.CharField(max_length=50, null=True, verbose_name='Temporary Voice Name', blank=True)
    temp_user_id = models.BigIntegerField(null=True, verbose_name='Temporary User ID', blank=True)
    temp_voice_tags = models.ManyToManyField(
        VoiceTag, 'user_voice_tags', blank=True, verbose_name='Temporary Voice Tags'
    )
    last_usage_date = models.DateTimeField(auto_now=True)
    vote = models.BooleanField(verbose_name='Vote System', default=False)
    date = models.DateTimeField(verbose_name='Register Date', auto_now_add=True)
    voice_order = models.CharField(max_length=12, choices=VoiceOrder.choices, default=VoiceOrder.new_voice_id)
    favorite_voices = models.ManyToManyField('Voice', 'favorite_voices', blank=True)
    back_menu = models.CharField(max_length=50, null=True, blank=True)
    started = models.BooleanField('Started', default=False)
    last_start = models.DateTimeField(null=True, blank=True)
    last_broadcast = models.ForeignKey('Broadcast', models.SET_NULL, 'user_broadcast', null=True, blank=True)
    playlists = models.ManyToManyField('Playlist', 'user_playlist', blank=True)
    current_playlist = models.ForeignKey(
        'Playlist',
        models.SET_NULL,
        'user_current_playlist',
        blank=True, null=True,
        verbose_name='Current Playlist',
        default=None
    )
    current_voice = models.ForeignKey('Voice', models.SET_NULL, 'user_voice', blank=True, null=True, default=None)
    current_ad = models.ForeignKey('Ad', models.SET_NULL, 'user_ad', null=True, blank=True)
    menu_mode = models.CharField(
        max_length=1, verbose_name='Menu Mode', choices=MenuMode.choices, default=MenuMode.USER
    )
    recent_voices = models.ManyToManyField(
        'Voice', 'recent_voices', blank=True, verbose_name='Recent Voices', through='RecentVoice'
    )
    use_recent_voices = models.BooleanField('Use Recent Voices', default=True)

    class Meta:
        db_table = 'persianmeme_users'
        ordering = ['user_id']

    def __str__(self):
        return f'{self.chat_id}:{self.rank}'


class Voice(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'a', 'Active'
        PENDING = 'p', 'Pending'
        DELETED = 'd', 'Deleted'

    class Type(models.TextChoices):
        NORMAL = 'n', 'Normal'
        PRIVATE = 'p', 'Private'

    def ban_sender(self):
        self.sender.status = self.sender.Status.BANNED
        self.sender.save()
        self.deny()

    def delete(self, *args, **kwargs):
        if kwargs.get('log'):
            self.send_voice(
                settings.MEME_LOGS,
                kwargs.get('http_session', requests.Session()),
                voice_recovery(self.id),
                translations.admin_messages['deleted_by_admins'].format(
                    f' by {kwargs.pop("admin")}' if kwargs.get('admin') else '', self.file_id
                )
            )
            self.status = self.Status.DELETED
            return self.save()
        super().delete(*args, **kwargs)

    message_id = models.BigIntegerField(verbose_name='Message ID', null=True, blank=True)
    file_id = models.CharField(max_length=200, verbose_name='Voice File ID')
    file_unique_id = models.CharField(max_length=100, verbose_name='Voice Unique ID')
    name = models.CharField(max_length=200)
    sender = models.ForeignKey(User, models.CASCADE, related_name='senders')
    voters = models.ManyToManyField(User, related_name='voters', blank=True)
    votes = models.IntegerField(default=0, verbose_name='Up Votes')
    status = models.CharField(max_length=1, choices=Status.choices)
    date = models.DateTimeField(auto_now_add=True, verbose_name='Register Date')
    voice_type = models.CharField(max_length=1, choices=Type.choices, default=Type.NORMAL)
    accept_vote = models.ManyToManyField(User, 'accept_vote_users', blank=True, verbose_name='Accept Votes')
    deny_vote = models.ManyToManyField(User, 'deny_vote_users', blank=True, verbose_name='Deny Votes')
    tags = models.ManyToManyField(VoiceTag, 'voice_tags', blank=True)
    usage_count = models.PositiveIntegerField('Usage Count', default=0)
    assigned_admin = models.ForeignKey(
        User, models.SET_NULL, 'voice_admin', verbose_name='Assigned Admin', null=True, blank=True
    )
    reviewed = models.BooleanField('Is Reviewed', default=False)

    class Meta:
        db_table = 'persianmeme_voices'
        ordering = ['-id']

    def __str__(self):
        return f'{self.name}:{self.file_id}'

    def user_accept(self):
        self.status = self.Status.ACTIVE
        self.save()
        self.accept_vote.clear()
        self.deny_vote.clear()
        return self.sender

    def user_deny(self):
        sender = self.sender
        self.delete()
        return sender

    def accept(self):
        from .functions import send_message
        self.status = self.Status.ACTIVE
        self.save()
        self.accept_vote.clear()
        self.deny_vote.clear()
        send_message(self.sender.chat_id, translations.user_messages['voice_accepted'])
        for admin in User.objects.filter(rank=User.Rank.ADMIN):
            send_message(admin.chat_id, translations.admin_messages['review_required'])

    def deny(self):
        from .functions import send_message
        send_message(self.sender.chat_id, translations.user_messages['voice_denied'])
        self.delete()

    @sync_fix
    def send_voice(
            self,
            chat_id: int,
            session: requests.Session = requests.Session(),
            voice_keyboard: dict = None,
            extra_text: str = ''
    ) -> int:
        tags_string = str()
        for tag in self.tags.all():
            tags_string += f'\n<code>{tag.tag}</code>'
        voice_dict = {
            'caption': f'{extra_text}<b>Voice Name</b>: <code>{self.name}</code>\n\n<b>Voice Tags 👇</b>{tags_string}',
            'parse_mode': 'HTML',
            'voice': self.file_id,
            'chat_id': chat_id
        }
        if voice_keyboard:
            voice_dict['reply_markup'] = json.dumps(voice_keyboard)
        with session.get(
                f'https://api.telegram.org/bot{settings.MEME}/sendVoice',
                params=voice_dict,
                timeout=settings.REQUESTS_TIMEOUT * 10
        ) as response:
            if response.status_code == 200:
                return response.json()['result']['message_id']
            elif response.status_code != 429:
                return 0
            raise TooManyRequests(response.json()['parameters']['retry_after'])


class Ad(models.Model):
    ad_id = models.AutoField(primary_key=True, verbose_name='Ad ID')
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
    voice = models.ForeignKey(Voice, models.CASCADE, 'deletes_voice')
    user = models.ForeignKey(User, models.CASCADE, 'deletes_user')

    class Meta:
        db_table = 'persianmeme_deletes'
        ordering = ['delete_id']

    def __str__(self):
        return f'{self.delete_id} : {self.voice.id}'


class Broadcast(models.Model):
    message_id = models.IntegerField('Message ID')
    sender = models.ForeignKey(User, models.CASCADE, 'broadcast_user', verbose_name='Sender Admin')
    sent = models.BooleanField('Is Sent', default=False)

    @property
    @sync_to_async
    def get_sender(self):
        return self.sender

    def __str__(self):
        return f'{self.id}:{self.message_id}'

    class Meta:
        db_table = 'persianmeme_broadcasts'
        ordering = ['id']


class Playlist(models.Model):
    invite_link = models.UUIDField('Invite ID', default=uuid4)
    name = models.CharField(max_length=60)
    voices = models.ManyToManyField(Voice, 'playlist_voice')
    creator = models.ForeignKey(User, models.CASCADE)
    date = models.DateTimeField('Creation Date', auto_now_add=True)

    def get_link(self):
        return f'https://t.me/Persian_Meme_Bot?start={self.invite_link}'

    class Meta:
        db_table = 'persianmeme_playlists'
        ordering = ['-date']

    def __str__(self):
        return f'{self.name}:{self.creator.chat_id}'


class Message(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 1, 'Pending'
        READ = 2, 'Read'

    sender = models.ForeignKey(User, models.CASCADE, 'message_user')
    message_id = models.PositiveBigIntegerField('Message ID')
    status = models.PositiveSmallIntegerField(choices=Status.choices, default=Status.PENDING)

    class Meta:
        db_table = 'persianmeme_messages'

    def __str__(self):
        return f'{self.id} : {self.sender.chat_id}'


class RecentVoice(models.Model):
    user = models.ForeignKey(User, models.CASCADE, 'recent_voice_user')
    voice = models.ForeignKey(Voice, models.CASCADE, 'recent_voice_voice')

    class Meta:
        ordering = ['-id']
        db_table = 'persianmeme_user_recent_voices'


BOT_ADMINS = (User.Rank.ADMIN, User.Rank.OWNER)
