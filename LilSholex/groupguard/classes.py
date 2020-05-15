from groupguard import models
import faster_than_requests as fast_req
from urllib.parse import urlencode
from django.conf import settings
import json
import datetime
from groupguard.translators import commands
from groupguard.decorators import fix
from groupguard import keyboards, functions, tasks


class User:
    """
    User class will be used to send messages and perform other actions via API .
    """

    def __init__(self, chat_id: int = None, /, *, instance: models.User = None):
        if chat_id:
            self.database, created = models.User.objects.get_or_create(chat_id=chat_id)
        else:
            assert instance, 'You must provide instance if there is not a chat_id !'
            self.database = instance

    @fix
    def send_message(
            self, text: str, /,
            reply_markup: dict = '',
            reply_to_message_id: int = '',
            parse_mode: str = None,
            disable_web_page_preview: bool = True
    ) -> int:

        if reply_markup != '':
            reply_markup = json.dumps(reply_markup)
        encoded = urlencode({'text': text, 'reply_markup': reply_markup})
        if (result := json.loads(fast_req.get(
            f'https://api.telegram.org/bot{settings.GROUP}/sendMessage?chat_id={self.database.chat_id}&{encoded}&'
            f'reply_to_message_id={reply_to_message_id}&parse_mode={parse_mode}&'
            f'disable_web_page_preview={disable_web_page_preview}'
        )['body']))['ok']:
            return result['result']['message_id']
        return 0

    @fix
    def get_chat(self) -> dict:
        result = json.loads(fast_req.get(
            f'https://api.telegram.org/bot{settings.GROUP}/getChat?chat_id={self.database.chat_id}'
        )['body'])['result']
        if result.get('first_name'):
            result['first_name'] = functions.clear_name(result['first_name'])
        return result

    def forward_message(self, from_chat_id: int, message_id: int) -> None:
        fast_req.get(
            f'https://api.telegram.org/bot{settings.GROUP}/forwardMessage?chat_id={self.database.chat_id}&from_chat_id='
            f'{from_chat_id}&message_id={message_id}'
        )

    def translate(self, cmd, /, *args):
        return commands[cmd][self.database.lang].format(*args)

    def keyboard(self, keyboard):
        return getattr(keyboards, f'{self.database.lang}_{keyboard}')


class Group(User):  # Using User class Methods in Group class
    """
    Group class will be used to perform actions related to groups via API .
    """

    def __init__(self, user: models.User = None, chat_id: int = None, /, *, instance: models.Group = None):
        if chat_id:
            assert user, 'You must provide a user with chat_id !'
            if (target_user := models.Group.objects.filter(chat_id=chat_id)).exists():
                self.database = target_user.first()
            else:
                self.database = models.Group.objects.create(chat_id=chat_id, owner=user)
        else:
            assert instance, 'You must use a instance or chat_id to create this object !'
            self.database = instance

    @fix
    def delete_message(self, message_id: int, /) -> None:
        fast_req.get(
            f'https://api.telegram.org/bot{settings.GROUP}/deleteMessage?chat_id={self.database.chat_id}&'
            f'message_id={message_id}'
        )

    def set_chat_title(self, title: str, /) -> None:
        fast_req.get(
            f'https://api.telegram.org/bot{settings.GROUP}/setChatTitle?chat_id={self.database.chat_id}&'
            f'title={title}'
        )

    def pin_chat_message(self, message_id: int, /) -> None:
        fast_req.get(
            f'https://api.telegram.org/bot{settings.GROUP}/pinChatMessage?chat_id={self.database.chat_id}&'
            f'message_id={message_id}'
        )
        self.send_message(self.translate('pin'), reply_to_message_id=message_id)

    def leave_chat(self) -> None:
        fast_req.get(f'https://api.telegram.org/bot{settings.GROUP}/leaveChat?chat_id={self.database.chat_id}')

    def set_chat_permissions(self, permissions: dict, /) -> None:
        fast_req.get(
            f'https://api.telegram.org/bot{settings.GROUP}/setChatPermissions?chat_id={self.database.chat_id}&'
            f'permissions={json.dumps(permissions)}'
        )

    def promote_chat_member(self, permissions: dict, /) -> None:
        encoded = urlencode(permissions)
        fast_req.get(
            f'https://api.telegram.org/bot{settings.GROUP}/promoteChatMember?chat_id={self.database.chat_id}&{encoded}'
        )

    def unpin_chat_message(self) -> None:
        fast_req.get(f'https://api.telegram.org/bot{settings.GROUP}/unpinChatMessage?chat_id={self.database.chat_id}')
        self.send_message(self.translate('unpin'))

    @fix
    def get_chat_member(self, user_id: int) -> dict:
        if(result := json.loads(fast_req.get(
            f'https://api.telegram.org/bot{settings.GROUP}/getChatMember?chat_id={self.database.chat_id}&'
            f'user_id={user_id}'
        )['body']))['ok']:
            return result['result']

    def unban_chat_member(self, from_user: dict, /) -> None:
        fast_req.get(
            f'https://api.telegram.org/bot{settings.GROUP}/unbanChatMember?chat_id={self.database.chat_id}&'
            f'user_id={from_user["id"]}'
        )
        self.send_message(self.translate('unban', from_user['first_name']))

    def kick_chat_member(self, user_id: int, first_name: str, reason: str, until_date: float = '', /):
        fast_req.get(
            f'https://api.telegram.org/bot{settings.GROUP}/kickChatMember?chat_id={self.database.chat_id}&'
            f'user_id={user_id}&until_date={until_date}'
        )
        for message in self.get_messages(40, User(user_id).database):
            self.delete_message(message.message_unique_id)
            message.delete()
        self.send_message(self.translate('ban', functions.clear_name(first_name), reason))

    def export_chat_invite_link(self, message_id):
        try:
            link = json.loads(fast_req.get2json(
                f'https://api.telegram.org/bot{settings.GROUP}/exportChatInviteLink?chat_id={self.database.chat_id}'
            ))['result']
        except fast_req.NimPyException:
            self.send_message(self.translate('bot_permission'), reply_to_message_id=message_id)
        else:
            self.send_message(self.translate('link', link), reply_to_message_id=message_id)

    @fix
    def get_chat_members_count(self):
        if (result := json.loads(fast_req.get(
            f'https://api.telegram.org/bot{settings.GROUP}/getChatMembersCount?chat_id={self.database.chat_id}'
        )['body']))['ok']:
            return result['result']
        return 0

    def restrict_chat_member(self, user_id: int, permissions: dict, until_date: float = '', /):
        fast_req.get(
            f'https://api.telegram.org/bot{settings.GROUP}/restrictChatMember?chat_id={self.database.chat_id}&'
            f'user_id={user_id}&permissions={json.dumps(permissions)}&until_date={until_date}'
        )

    @fix
    def get_chat_administrators(self):
        if (result := json.loads(fast_req.get(
            f'https://api.telegram.org/bot{settings.GROUP}/getChatAdministrators?'
            f'chat_id={self.database.chat_id}'
        )['body']))['ok']:
            return result['result']
        return ()

    def get_warns(self, user: models.User):
        warn, created = models.Warn.objects.get_or_create(user=user, group=self.database)
        warn.count -= (datetime.datetime.now() - warn.last_edit).days // self.database.clear_days
        warn.count = 0 if warn.count < 0 else warn.count
        warn.save()
        return warn

    def warn_user(self, user: User, reason, message_id, /):
        warn = self.get_warns(user.database)
        warn.count += 1
        try:
            models.Message.objects.filter(
                user=user.database, group=self.database, message_unique_id=message_id
            ).delete()
        except models.Message.DoesNotExist:
            pass
        self.delete_message(message_id)
        if warn.count >= self.database.max_warn:
            warn.count = 0
            warn.save()
            if self.database.max_warn_punish == 'b':
                self.kick_chat_member(
                    user.database.chat_id, user.get_chat()['first_name'], self.translate('max_warn')
                )
            else:
                self.restrict_chat_member(user.database.chat_id, {'can_send_messages': False})
                self.send_message(
                    self.translate('warn_mute', user.get_chat()['first_name'], user.database.chat_id),
                    parse_mode='Markdown'
                )
        else:
            warn.save()
            self.send_message(
                self.translate('warn', user.get_chat()['first_name'], user.database.chat_id, reason),
                parse_mode='Markdown'
            )

    def clear(self, from_user: dict, /):
        warn, created = models.Warn.objects.get_or_create(user=User(from_user['id']).database, group=self.database)
        from_user['first_name'] = functions.clear_name(from_user['first_name'])
        if warn.count > 0:
            warn.count = 0
            self.send_message(self.translate('clear', from_user['first_name'], from_user['id']), parse_mode='Markdown')
            warn.save()
        else:
            self.send_message(
                self.translate('no_warn', from_user['first_name'], from_user['id']), parse_mode='Markdown'
            )

    def login(self, user: models.User):
        user_login = models.Login.objects.filter(user=user, group=self.database)
        if user_login.exists() and (datetime.datetime.now() - user_login.first().creation_date).seconds / 60 <= 10:
            return user_login.first().login_token
        else:
            return models.Login.objects.create(user=user, group=self.database).login_token

    def check_spam(self, user: models.User, message: dict, user_perms: dict, activity_message: models.Message):
        current_time = datetime.datetime.fromtimestamp(message['date'])
        if not (activity := models.Activity.objects.filter(user=user, group=self.database)).exists():
            activity = models.Activity.objects.create(user=user, group=self.database, last_message=current_time)
        else:
            activity = activity.first()
        if activity.restricted:
            if user_perms['status'] in ('administrator', 'member', 'creator') or user_perms.get(
                    'can_send_messages', False
            ):
                activity.restricted = False
                activity.last_message = current_time
                activity.save()
            else:
                self.delete_message(message['message_id'])
        else:
            activity.count += 1
            activity.messages.add(activity_message)
            if (current_time - activity.last_message).seconds >= self.database.spam_time:
                activity.count = 1
                activity.last_message = current_time
                activity.messages.clear()
                activity.save()
            else:
                activity.last_message = current_time
                if activity.count >= self.database.max_messages:
                    activity.count = 0
                    activity.restricted = True
                    activity.save()
                    for activity_message in activity.messages.all():
                        self.delete_message(activity_message.message_unique_id)
                    activity.messages.all().delete()
                    message['from']['first_name'] = functions.clear_name(message['from']['first_name'])
                    if self.database.spam_punish == 'b':
                        self.kick_chat_member(user.chat_id, message['from']['first_name'], self.translate('spamming'))
                    else:
                        self.restrict_chat_member(user.chat_id, {'can_send_messages': False})
                        self.send_message(
                            self.translate('spam', message['from']['first_name'], user.chat_id), parse_mode='Markdown'
                        )
                else:
                    activity.save()

    def check_report(self, message_id: int, message_unique_id: int, user: models.User):
        message, created = models.Message.objects.get_or_create(
            message_unique_id=message_unique_id, group=self.database
        )
        if user not in message.reporters.all():
            message.reporters.add(user)
            message.reports += 1
            if message.reports >= self.database.max_reports:
                self.delete_message(message.message_unique_id)
                self.send_message(self.translate('max_report'), reply_to_message_id=message_id)
                message.delete()
            else:
                self.send_message(self.translate('report'), reply_to_message_id=message_id)
                message.save()
        else:
            self.send_message(self.translate('already_report'), reply_to_message_id=message_id)

    def send_message(
            self,
            text: str,
            /,
            reply_markup: dict = '',
            reply_to_message_id: int = '',
            parse_mode: str = None,
            delete: bool = True,
            disable_web_page_preview: bool = True
    ):
        message_id = super().send_message(text, reply_markup, reply_to_message_id, parse_mode, disable_web_page_preview)
        if self.database.deleting and delete:
            tasks.bot_message(self.database.chat_id, message_id, schedule=self.database.delete_time)

    def get_add(self, user: models.User):
        if (target_add := models.ForcedAdd.objects.filter(group=self.database, user=user)).exists():
            return target_add.first()
        return models.ForcedAdd.objects.create(group=self.database, user=user)

    def noadd(self, user):
        force_add = self.get_add(user.database)
        force_add.promoted = True
        force_add.save()
        self.restrict_chat_member(user.database.chat_id, self.get_chat()['permissions'])
        self.send_message(
            self.translate('noadd', functions.clear_name(user.get_chat()['first_name']), user.database.chat_id),
            parse_mode='Markdown'
        )

    def get_messages(self, count: int, user: models.User = None, /):
        if user:
            return models.Message.objects.filter(group=self.database, user=user)[:count]
        return models.Message.objects.filter(group=self.database)[:count]

    def lockdown(self):
        self.database.last_permissions = json.dumps(self.get_chat()['permissions'])
        self.set_chat_permissions({'can_send_messages': False})

    def unlock(self):
        self.set_chat_permissions(json.loads(self.database.last_permissions))
        self.database.last_permissions = None


class Violation(Exception):
    """
    This exception class will be used to detect violations in locks .
    """
    pass
