import json
from urllib.parse import urlencode
import requests
from django.conf import settings
from django.db import models
from LilSholex.decorators import fix
from .keyboards import voice as voice_keyboard


class User(models.Model):
    class Status(models.TextChoices):
        active = 'a', 'Active'
        banned = 'b', 'Banned'
        full_banned = 'f', 'Full Banned'

    class Rank(models.TextChoices):
        owner = 'o', 'Owner'
        user = 'u', 'User'
        admin = 'a', 'Admin'
        khiar = 'k', 'Khiar'

    class VoiceOrder(models.TextChoices):
        votes = 'votes', 'Votes (Low to High)'
        voice_id = 'voice_id', 'Voice ID (Old to New)'
        high_votes = '-votes', 'Votes (High to Low)'
        new_voice_id = '-voice_id', 'Voice ID (New to Old)'

    user_id = models.AutoField(verbose_name='User ID', primary_key=True, unique=True)
    chat_id = models.BigIntegerField(verbose_name='User Chat ID', unique=True)
    menu = models.IntegerField(verbose_name='Current Menu', default=1)
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.active,
        verbose_name='Current Status'
    )
    rank = models.CharField(max_length=1, choices=Rank.choices, default=Rank.user, verbose_name='User Rank')
    sent_message = models.BooleanField(verbose_name='Sent Message', default=False)
    username = models.CharField(max_length=35, verbose_name='Username', null=True, blank=True)
    temp_voice_name = models.CharField(max_length=50, null=True)
    temp_user_id = models.BigIntegerField(null=True)
    last_date = models.BigIntegerField()
    count = models.IntegerField(default=1)
    last_usage_date = models.DateTimeField(auto_now=True, verbose_name='Last Usage Date')
    vote = models.BooleanField(verbose_name='Vote System', default=False)
    date = models.DateTimeField(verbose_name='Register Date', auto_now_add=True)
    voice_order = models.CharField(max_length=9, choices=VoiceOrder.choices, default=VoiceOrder.new_voice_id)
    private_voices = models.ManyToManyField('Voice', 'private_voices', verbose_name='Private Voices')
    favorite_voices = models.ManyToManyField('Voice', 'favorite_voices', verbose_name='Favorite Voices')
    back_menu = models.CharField(max_length=50, null=True, blank=True)
    started = models.BooleanField('Started', default=False)

    class Meta:
        db_table = 'persianmeme_users'
        ordering = ['user_id']

    def __str__(self):
        return f'{self.chat_id}:{self.rank}'


class Voice(models.Model):
    class Status(models.TextChoices):
        active = 'a', 'Active'
        pending = 'p', 'Pending'

    class Type(models.TextChoices):
        normal = 'n', 'Normal'
        private = 'p', 'Private'

    def delete(self, *args, **kwargs):
        if not kwargs.get('dont_send'):
            from .classes import User as UserClass
            owner = UserClass(instance=User.objects.filter(rank=User.Rank.owner).first())
            admin = f' by {kwargs.pop("admin")}' if kwargs.get('admin') else ''
            owner.send_message(f'Voice has been deleted{admin} !\nName : {self.name}\nFile ID : {self.file_id}')
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
    voice_type = models.CharField(max_length=1, choices=Type.choices, default=Type.normal, verbose_name='Voice Type')
    accept_vote = models.ManyToManyField(User, 'accept_vote_users', blank=True, verbose_name='Accept Votes')
    deny_vote = models.ManyToManyField(User, 'deny_vote_users', blank=True, verbose_name='Deny Votes')

    class Meta:
        db_table = 'persianmeme_voices'
        ordering = ['-voice_id']

    def __str__(self):
        return f'{self.name}:{self.file_id}'

    def accept(self):
        from .functions import send_message
        self.status = 'a'
        self.save()
        send_message(self.sender.chat_id, 'ویس ارسالی شما توسط مدیر ربات تایید شد ✅')

    def deny(self):
        from .functions import send_message
        send_message(self.sender.chat_id, 'ویس ارسالی شما توسط مدیر ربات رد شد ❌')
        self.delete(dont_send=True)

    def get_sender(self):
        return self.sender

    def get_voters_admin(self):
        return list(self.accept_vote.all()), list(self.deny_vote.all())

    def edit_vote_count(self, message_id: int):
        accept_votes, deny_votes = self.get_voters_admin()
        accept_voters = '\n\t'.join(
            [f'<a href="tg://user?id={user.chat_id}">{user.chat_id}</a>' for user in accept_votes]
        )
        deny_voters = '\n\t'.join(
            [f'<a href="tg://user?id={user.chat_id}">{user.chat_id}</a>' for user in deny_votes]
        )
        caption = (
            f'<b>Sender</b>: {(self.get_sender()).chat_id}\n'
            f'<b>Voice Info</b>: {self.name}\n\n'
            f'<b>Accept Voters</b>:\n\t{accept_voters}\n\n'
            f'<b>Deny Voters</b>:\n\t{deny_voters}'
        )
        encoded = urlencode({
            'caption': caption,
            'parse_mode': 'Html',
            'reply_markup': json.dumps(voice_keyboard(len(accept_votes), len(deny_votes)))
        })
        requests.get(
            f'https://api.telegram.org/bot{settings.MEME}/editMessageCaption?chat_id={settings.MEME_CHANNEL}&'
            f'message_id={message_id}&{encoded}'
        )

    @fix
    def send_voice(self) -> int:
        encoded = urlencode({
            'caption': f'<b>Sender</b>: {self.sender.chat_id}\n<b>Voice Info</b>: {self.name}',
            'parse_mode': 'Html',
            'reply_markup': json.dumps(voice_keyboard())
        })
        response = requests.get(
                f'https://api.telegram.org/bot{settings.MEME}/sendVoice?chat_id={settings.MEME_CHANNEL}&'
                f'voice={self.file_id}&{encoded}'
        ).json()
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

    def get_voice(self):
        return self.voice

    def get_user(self):
        return self.user


class Broadcast(models.Model):
    message_id = models.IntegerField('Message ID')
    sender = models.ForeignKey(User, models.CASCADE, 'broadcast_user', verbose_name='Sender Admin')
    sent = models.BooleanField('Sent', default=False)
