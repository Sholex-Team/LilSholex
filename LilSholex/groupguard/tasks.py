from background_task import background
from groupguard import models, classes
from groupguard.functions import tehran_time
from groupguard.decorators import fix
from django.conf import settings
from datetime import datetime
import requests


@background
@fix
def bot_message(chat_id: int, message_id: int, /):
    requests.get(
        f'https://api.telegram.org/bot{settings.GROUP}/deleteMessage?chat_id={chat_id}&message_id={message_id}'
    )


@background(schedule=1)
def add(group_id: int, user_id: int, added_count: int, /):
    user = classes.User(user_id)
    group = classes.Group(user.database, group_id)
    if user_perms := group.get_chat_member(user.database.chat_id):
        force_add = group.get_add(user.database)
        force_add.added_number += added_count
        force_add.save()
        if (remain := group.database.force_count - force_add.added_number) > 0:
            group.send_message(group.translate(
                'add_more',
                user_perms['user']['first_name'],
                user.database.chat_id,
                remain
            ), parse_mode='Markdown')
        else:
            group.restrict_chat_member(user.database.chat_id, group.get_chat()['permissions'])
            group.send_message(
                group.translate('unmute', user_perms['user']['first_name'], user.database.chat_id),
                parse_mode='Markdown'
            )


@background(schedule=5)
def check_lock(group_id):
    group = classes.Group(instance=models.Group.objects.filter(chat_id=group_id).first())
    if group.database.auto_lock:
        if group.database.auto_lock_off > (
                current_time := tehran_time(datetime.now()).time()
        ) >= group.database.auto_lock_on and not group.database.last_permissions:
            group.lockdown()
            group.database.save()
            group.send_message(group.translate('auto_lock_on'), delete=False)
        elif current_time >= group.database.auto_lock_off and group.database.last_permissions:
            group.unlock()
            group.database.save()
            group.send_message(group.translate('auto_lock_off'), delete=False)
        check_lock(group.database.chat_id)
    else:
        group.database.is_checking = False
        group.database.save()
