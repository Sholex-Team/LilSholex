from django.db import models
from uuid import uuid4


class User(models.Model):
    class Status(models.TextChoices):
        active = 'a', 'Active'
        banned = 'b', 'Banned'

    class Rank(models.TextChoices):
        admin = 'a', 'Admin'
        user = 'u', 'User'

    chat_id = models.BigIntegerField(verbose_name='User ID', primary_key=True)
    token = models.UUIDField(default=uuid4, verbose_name='Token', unique=True)
    username = models.CharField(max_length=64, verbose_name='Username', null=True, blank=True)
    last_menu = models.IntegerField(verbose_name='Last Menu', null=True, blank=True)
    nick_name = models.CharField(max_length=64, verbose_name='Nick Name', null=True, blank=True)
    last_usage_date = models.DateTimeField(auto_now=True, verbose_name='Last Usage Date')
    menu = models.IntegerField(verbose_name='Current Menu', default=1)
    status = models.CharField(
        max_length=1, choices=Status.choices, default=Status.active, verbose_name='Current Status'
    )
    rank = models.CharField(max_length=1, choices=Rank.choices, default=Rank.user, verbose_name='User Rank')
    token_last_receiver = models.UUIDField(verbose_name='Token Receiver', null=True, blank=True)
    black_list = models.ManyToManyField('User', 'users_block', verbose_name='Black List', blank=True)

    class Meta:
        ordering = ['-last_usage_date']
        db_table = 'anonymous_users'

    def __str__(self):
        return f'{self.chat_id} : {self.username}'


class Message(models.Model):
    class Type(models.TextChoices):
        message = 'm', 'Message'
        reply = 'r', 'Reply'

    message_id = models.BigIntegerField(verbose_name='Message ID', primary_key=True)
    text = models.TextField(verbose_name='Text Message')
    sender = models.ForeignKey(
        User, models.SET_NULL, 'messages_sender', null=True, blank=True, verbose_name='User Sender'
    )
    receiver = models.ForeignKey(
        User, models.SET_NULL, 'messages_receiver', null=True, blank=True, verbose_name='User Receiver'
    )
    sending_date = models.DateTimeField(auto_now_add=True, verbose_name='Sending Date')
    is_read = models.BooleanField(verbose_name='Is Read', default=False)
    reading_date = models.DateTimeField(auto_now=True, verbose_name='Reading Date')
    message_type = models.CharField(max_length=1, choices=Type.choices, verbose_name='Message Type')

    class Meta:
        ordering = ['-message_id']
        db_table = 'anonymous_messages'

    def __str__(self):
        return f'{self.message_id} : {self.sender}'
