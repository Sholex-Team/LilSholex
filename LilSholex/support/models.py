from django.db import models


class Message(models.Model):
    class Webapp(models.TextChoices):
        group = 'g', 'Group Manager'
        movie = 'm', 'Movie'
        anonymous = 'a', 'Anonymous'

    class Type(models.TextChoices):
        suggestion = 's', 'Suggestion'
        bug = 'b', 'Bug'

    message_id = models.AutoField(primary_key=True, verbose_name='Message ID')
    message_unique_id = models.IntegerField(verbose_name='Message Unique ID')
    webapp = models.CharField(
        max_length=1, verbose_name='Support Webapp', choices=Webapp.choices, null=True, blank=True
    )
    text = models.TextField(verbose_name='Message')
    sending_date = models.DateTimeField(auto_now_add=True, verbose_name='Sending Date')
    admin = models.ForeignKey(
        'User', models.SET_NULL, 'messages_admin', null=True, blank=True, verbose_name='Message Admin'
    )
    answering_date = models.DateTimeField(verbose_name='Answering Date', null=True, blank=True)
    message_type = models.CharField(max_length=1, verbose_name='Message Type', choices=Type.choices)

    class Meta:
        ordering = ['sending_date']
        db_table = 'support_messages'

    def __str__(self):
        return f'{self.message_id} : {self.message_unique_id}'


class User(models.Model):
    class Rank(models.TextChoices):
        admin = 'a', 'Admin'
        user = 'u', 'User'

    class Status(models.TextChoices):
        active = 'a', 'Active'
        banned = 'b', 'Banned'

    class Lang(models.TextChoices):
        english = 'en', 'English'
        persian = 'fa', 'Persian'

    chat_id = models.BigIntegerField(verbose_name='Chat ID', primary_key=True)
    menu = models.IntegerField(verbose_name='Current Menu', default=1)
    rank = models.CharField(max_length=1, verbose_name='Rank', choices=Rank.choices, default=Rank.user)
    register_date = models.DateTimeField(auto_now_add=True, verbose_name='Register Date')
    lang = models.CharField(max_length=2, verbose_name='Language', choices=Lang.choices, default=Lang.english)
    last_activity = models.DateTimeField(auto_now=True, verbose_name='Last Activity')
    current_message = models.ForeignKey(
        Message, models.SET_NULL, 'users_message', verbose_name='Current Message', null=True, blank=True
    )
    status = models.CharField(max_length=1, verbose_name='Status', choices=Status.choices, default=Status.active)
    current_type = models.CharField(
        max_length=1, choices=Message.Type.choices, verbose_name='Current Message Type', null=True, blank=True
    )
    current_webapp = models.CharField(
        max_length=1, verbose_name='Current Webapp', choices=Message.Webapp.choices, null=True, blank=True
    )

    def __str__(self):
        return f'{self.chat_id} : {self.menu}'

    class Meta:
        ordering = ['last_activity']
        db_table = 'support_users'
