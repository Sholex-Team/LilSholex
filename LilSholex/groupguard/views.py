import json
from groupguard import keyboards, models, forms, classes, functions, tasks
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from string import ascii_letters
from ipware import get_client_ip
import datetime
from django.conf import settings
from re import search


@require_POST
@csrf_exempt
def webhook(request):
    models.Message.objects.filter(date__lt=datetime.datetime.now() - datetime.timedelta(days=2)).delete()
    """
    This view function will be used as a webhook .
    """
    update = json.loads(request.body.decode())
    if 'callback_query' in update:
        validation = models.Verify.objects.get(verify_id=update['callback_query']['data'])
        group = classes.Group(instance=validation.group)
        message_id = update['callback_query']['message']['message_id']
        callback_id = update['callback_query']['id']
        data = update['callback_query']['data']
        if validation.validated or validation.valid_until < datetime.datetime.now():
            group.delete_message(message_id)
            functions.answer_callback_query(callback_id, group.translate('expired'), True)
        elif validation.user.chat_id == (user_id := update['callback_query']['from']['id']):
            validation.validated = True
            functions.answer_callback_query(callback_id, group.translate('verified'), True)
            group.delete_message(message_id)
            group.restrict_chat_member(user_id, group.get_chat()['permissions'])
            validation.save()
        if search('^change_(.*)_lock\S(-.*)', data):
            chat_id = search('^change_(.*)_lock\S(-.*)', data).group(2)
            lockType = search('^change_(.*)_lock\S(-.*)', data).group(1) + '_lock'
            user = classes.User(update['callback_query']['from']['id'])
            group = classes.Group(user.database, chat_id)
            user_perms = group.get_chat_member(user.database.chat_id)
            if user_perms['status'] in ('administrator', 'creator') or user_perms['can_restrict_members']:
                getattr(group.database, lockType)
                setattr(group.database, lockType, True)
                keyboard = keyboards.inlinePanel(chat_id, update['callback_query']['from']['id'])
                if user.database.lang == 'fa':
                    keyboard = keyboard['fa']
                    answer = 'انجام شد !'
                else:
                    keyboard = keyboard['en']
                    answer = 'Done !'
                functions.answer_callback_query(callback_id, answer, True)
                user.edit_message_keyboard(update['callback_query']['from']['id'], message_id, keyboard)

        return HttpResponse(status=200)
    elif 'message' in update:
        message = update['message']
    elif 'edited_message' in update:
        message = update['edited_message']
    else:
        return HttpResponse(status=200)
    if message['from']['id'] == 777000:
        return HttpResponse(200)
    if (text := message.get('text', 'None')) in ('.', '/'):
        text = 'None'
    message_id = message['message_id']
    if message['chat']['id'] > 0:
        user = classes.User(message['chat']['id'])
        try:
            user.database.username = '@' + message['chat']['username'].lower()
        except KeyError:
            user.database.username = None
        if user.database.rank == 'a':
            if text == '/start':
                user.send_message('Welcome to admin panel !', keyboards.admin, message['message_id'],
                                  parse_mode='Markdown')
                user.database.menu = 1
            else:
                if user.database.menu == 1:
                    if text == 'Groups':
                        user.send_message(f'Groups count : {models.Group.objects.count()} !')
                    elif text == 'Users':
                        user.send_message(f'Users count : {models.User.objects.count()} !')
                    elif text == 'Ban Group':
                        user.database.menu = 2
                        user.send_message('Please send the group Chat ID .', keyboards.en_back)
                    elif text == 'Ban User':
                        user.database.menu = 3
                        user.send_message('Please send the user Chat ID .', keyboards.en_back)
                    elif text == 'Unban Group':
                        user.database.menu = 4
                        user.send_message('Please send the group Chat ID to be unbanned .', keyboards.en_back)
                    elif text == 'Unban User':
                        user.database.menu = 5
                        user.send_message('Please send the user Chat ID to be unbanned .', keyboards.en_back)
                    elif text == 'Add Ad':
                        user.database.menu = 6
                        user.send_message('Please send a message as Ad .', keyboards.en_back)
                    elif text == 'Delete Ad':
                        user.database.menu = 7
                        user.send_message('Please send an Ad ID .', keyboards.en_back)
                    else:
                        user.send_message('Unknown message ⚠️')
                elif user.database.menu == 2:
                    if text == 'Back 🔙':
                        user.database.menu = 1
                        user.send_message('You are at main menu !', keyboards.admin)
                    else:
                        try:
                            group_id = int(text)
                        except ValueError:
                            user.send_message('Please provide a negative number as Group ID !')
                        else:
                            if group_id > 0:
                                user.send_message('Please provide a negative value .')
                            else:
                                group = classes.Group(user.database, group_id)
                                group.database.status = 'b'
                                group.database.save()
                                user.database.menu = 1
                                user.database.menu = 1
                                user.send_message('This group has been banned 📛', keyboards.admin)
                elif user.database.menu == 3:
                    if text == 'Back 🔙':
                        user.database.menu = 1
                        user.send_message('You are at main menu !', keyboards.admin)
                    else:
                        try:
                            user_id = int(text)
                        except ValueError:
                            user.send_message('Please provide a positive number as User ID !')
                        else:
                            if user_id < 0:
                                user.send_message('Please provide a positive value .')
                            else:
                                target_user = classes.User(user_id)
                                target_user.database.status = 'b'
                                target_user.database.save()
                                user.database.menu = 1
                                user.send_message('This user has been banned 📛', keyboards.admin)
                elif user.database.menu == 4:
                    if text == 'Back 🔙':
                        user.database.menu = 1
                        user.send_message('You are at main menu !', keyboards.admin)
                    else:
                        try:
                            user_id = int(text)
                        except ValueError:
                            user.send_message('Group ID is not valid !')
                        else:
                            if user_id > 0:
                                user.send_message('Group ID must be smaller than 0 !')
                            else:
                                try:
                                    target_user = models.Group.objects.get(chat_id=user_id)
                                except models.Group.DoesNotExist:
                                    user.send_message('Group does not exists .')
                                else:
                                    target_user.status = 'a'
                                    target_user.save()
                                    user.database.menu = 1
                                    user.send_message('Group has been unbanned ❌', keyboards.admin)
                elif user.database.menu == 5:
                    if text == 'Back 🔙':
                        user.database.menu = 1
                        user.send_message('You are at main menu !', keyboards.admin)
                    else:
                        try:
                            user_id = int(text)
                        except ValueError:
                            user.send_message('User ID is not valid !')
                        else:
                            if user_id < 0:
                                user.send_message('User ID must be bigger than 0 !')
                            else:
                                try:
                                    group = models.User.objects.get(chat_id=user_id)
                                except models.User.DoesNotExist:
                                    user.send_message('User does not exists .')
                                else:
                                    group.database.status = 'a'
                                    group.save()
                                    user.database.menu = 1
                                    user.send_message('User has been unbanned ❌', keyboards.admin)
                elif user.database.menu == 6:
                    if text == 'Back 🔙':
                        user.database.menu = 1
                        user.send_message('You are back at main menu .', keyboards.admin)
                    else:
                        ad, created = models.Ad.objects.get_or_create(
                            chat_id=user.database.chat_id, message_id=message_id
                        )
                        if created:
                            user.database.menu = 1
                            user.send_message(f'Ad has been added to list ✅\nAd ID : {ad.ad_id}', keyboards.admin)
                        else:
                            user.send_message(
                                f'This ad already exists !\nAd ID : {ad.ad_id}', reply_to_message_id=message_id
                            )
                elif user.database.menu == 7:
                    if text == 'Back 🔙':
                        user.database.menu = 1
                        user.send_message('You are back at main menu .', keyboards.admin)
                    else:
                        if text.isdigit():
                            try:
                                models.Ad.objects.get(ad_id=text).delete()
                            except models.Ad.DoesNotExist:
                                user.send_message('This Ad ID is invalid ✖️', reply_to_message_id=message_id)
                            else:
                                user.database.menu = 1
                                user.send_message('AD has been deleted !', keyboards.admin)
                        else:
                            user.send_message('Ad ID can only be a positive number !', reply_to_message_id=message_id)
        elif user.database.status == 'a':
            if not (
                    result := functions.get_chat_member('@SholexTeam', user.database.chat_id)
            ) or result['status'] not in ('administrator', 'creator', 'member'):
                user.send_message(user.translate('join_channel'), reply_to_message_id=message_id)
            elif text == '/start':
                user.database.menu = 1
                user.send_message(user.translate('start'), user.keyboard('user'))
            elif user.database.menu == 1:
                if text in ('Add to Group', 'اضافه کردن به گروه ⏬'):
                    user.send_message(user.translate('add_group'), reply_to_message_id=message_id)
                elif text in ('پشتیبانی 👨‍💻', 'Support'):
                    user.send_message(user.translate('support'), keyboards.support('t.me/SholexSupportbot'))
                elif text in ('Help 🆘', 'راهنما 📕'):
                    user.database.menu = 4
                    user.send_message(user.translate('help'), user.keyboard('help'))
                elif text in ('زبان 📖', 'Language 📖'):
                    user.database.menu = 2
                    user.send_message(user.translate('language'), user.keyboard('lang'))
                elif text in ('Validation 🔐', 'احراز هویت 🔐'):
                    user.database.menu = 3
                    user.send_message(user.translate('number'), user.keyboard('number'))
                else:
                    user.send_message(user.translate('unknown'))
            elif user.database.menu == 2:
                if text in ('بازگشت 🔙', 'Back 🔙'):
                    user.database.menu = 1
                    user.send_message(user.translate('back_main'), user.keyboard('user'))
                elif text == 'فارسی 🇮🇷':
                    user.database.lang = 'fa'
                    user.database.menu = 1
                    user.send_message('زبان به فارسی تغییر کرد 🇮🇷', keyboards.fa_user)
                elif text == 'English 🇺🇸':
                    user.database.lang = 'en'
                    user.database.menu = 1
                    user.send_message('Language changed to English 🇺🇸', keyboards.en_user)
                else:
                    user.send_message(user.translate('unknown'), reply_to_message_id=message_id)
            elif user.database.menu == 3:
                if text in ('بازگشت 🔙', 'Back 🔙'):
                    user.database.menu = 1
                    user.send_message(user.translate('back_main'), user.keyboard('user'))
                elif 'contact' in message and message['contact'].get('user_id', None) == user.database.chat_id:
                    user.database.phone_number = message['contact']['phone_number'].strip('+')
                    user.database.menu = 1
                    user.send_message(user.translate('number_verified'), user.keyboard('user'))
                    not_solved = []
                    for group in user.database.mutes.all():
                        if str(user.database.phone_number).startswith(str(group.number_range)):
                            group = classes.Group(user.database, instance=group)
                            group.restrict_chat_member(user.database.chat_id, group.get_chat()['permissions'])
                        else:
                            not_solved.append(group)
                    user.database.mutes.set(not_solved)
                else:
                    user.send_message(user.translate('invalid_number'), reply_to_message_id=message_id)
            elif user.database.menu == 4:
                if text in ('Back 🔙', 'بازگشت 🔙'):
                    user.database.menu = 1
                    user.send_message(user.translate('back_main'), user.keyboard('user'))
                elif text in ('Admin 💂‍♀️', 'دستورات ادمین 💂‍♀️'):
                    user.send_message(user.translate('admin_help'), reply_to_message_id=message_id)
                elif text in ('دستورات کلی 👨', 'General 👨'):
                    user.send_message(user.translate('general_help'), reply_to_message_id=message_id)
                elif text in ('دستورات سازنده 👨‍💻', 'Creator 👨‍💻'):
                    user.send_message(user.translate('creator_help'), reply_to_message_id=message_id)
                else:
                    user.send_message(user.translate('unknown'), reply_to_message_id=message_id)
        user.database.save()
    else:
        user = classes.User(message['from']['id'])
        try:
            user.database.username = '@' + message['from']['username'].lower()
        except KeyError:
            user.database.username = None
        group = classes.Group(user.database, message['chat']['id'])
        if group.database.status == 'b':
            group.send_message(group.translate('group_bannned'))
            group.leave_chat()
            user.database.save()
            group.database.save()
            return HttpResponse(status=200)
        if (
                member_count := group.get_chat_members_count()
        ) > 150 and not group.database.promoted and group.database.status != 'w':
            group.database.status = 'w'
            group.send_message(group.translate('ads'))
        elif member_count <= 150 or group.database.promoted:
            group.database.status = 'a'
        if group.database.status == 'w':
            for ad in models.Ad.objects.exclude(seen=group.database):
                group.forward_message(ad.chat_id, ad.message_id)
                ad.seen.add(group.database)
        if not any(admin['user'].get('username', None) == 'SholexBot' for admin in group.get_chat_administrators()):
            group.send_message(group.translate('bot_admin'))
            user.database.save()
            group.database.save()
            return HttpResponse(status=200)
        if group.database.services_lock and any(value in message for value in (
                'new_chat_title',
                'new_chat_photo',
                'delete_chat_photo',
                'left_chat_member',
                'pinned_message',
                'new_chat_members'
        )):
            group.delete_message(message_id)
            if 'new_chat_members' not in message:
                group.database.save()
                user.database.save()
                return HttpResponse(status=200)
        user_perms = group.get_chat_member(user.database.chat_id)
        # Welcome message for non bot users
        if group.database.is_welcome_message and 'new_chat_members' in message:
            text_is_cmd = False
            for new_user in message['new_chat_members']:
                if not new_user['is_bot']:
                    group.send_message(
                        group.database.welcome_message.replace(
                            '"first_name"',
                            f'[{functions.clear_name(new_user["first_name"])}](tg://user?id={new_user["id"]})'
                        ).replace(
                            '"group_name"',
                            group.get_chat()['title']
                        ), parse_mode='Markdown'
                    )
        else:
            # Saving message in database
            if not (activity_message := models.Message.objects.filter(
                    message_unique_id=message_id, group=group.database, user=user.database
            )).exists():
                activity_message = models.Message.objects.create(
                    message_unique_id=message_id, group=group.database, user=user.database
                )
            else:
                activity_message = activity_message.first()
            if user_perms['status'] not in ('administrator', 'creator'):
                if group.database.number_range and group.database not in user.database.number_pass.all():
                    if user.database.phone_number:
                        if not str(user.database.phone_number).startswith(str(group.database.number_range)):
                            group.restrict_chat_member(user.database.chat_id, {'can_send_messages': False})
                            group.send_message(group.translate('not_allowed_number'), reply_to_message_id=message_id)
                            if group.database not in user.database.mutes.all():
                                user.database.mutes.add(group.database)
                    else:
                        group.restrict_chat_member(user.database.chat_id, {'can_send_messages': False})
                        group.send_message(
                            group.translate('verify_number', user_perms['user']['first_name'], user.database.chat_id),
                            keyboards.verify_number,
                            parse_mode='Markdown'
                        )
                        if group.database not in user.database.mutes.all():
                            user.database.mutes.add(group.database)
                        group.database.save()
                        user.database.save()
                        return HttpResponse(status=200)
                if group.database.force_count:
                    target_add = group.get_add(user.database)
                    if not target_add.promoted and target_add.added_number < group.database.force_count \
                            and 'new_chat_members' not in message:
                        group.restrict_chat_member(
                            user.database.chat_id, {'can_send_messages': False, 'can_invite_users': True}
                        )
                        group.send_message(group.translate(
                            'forced_add',
                            user_perms['user']['first_name'],
                            user.database.chat_id,
                            group.database.force_count,
                        ), parse_mode='Markdown', delete=False)
                if 'edited_message' not in update:
                    group.check_spam(user.database, message, user_perms, activity_message)
                if group.database.channel and (
                        not (result := functions.get_chat_member(
                            group.database.channel, user.database.chat_id)
                        ) or result['status'] not in ('creator', 'administrator', 'member')
                ):
                    group.delete_message(message_id)
                    group.send_message(
                        group.translate('channel', user_perms['user']['first_name'], user.database.chat_id),
                        keyboards.invite('t.me/' + group.database.channel[1:]),
                        parse_mode='Markdown'
                    )
                    user.database.save()
                    group.database.save()
                    return HttpResponse(status=200)
            if text.startswith(('/', '.')):
                if len((new_text := text.replace('@SholexBot', ''))) != 1:
                    text = new_text
                if user_perms['status'] in ('administrator', 'creator') and (not (
                        result := functions.get_chat_member('@SholexTeam', user.database.chat_id)
                ) or result['status'] not in ('administrator', 'member', 'creator')):
                    group.send_message(group.translate('join_channel'))
                    user.database.save()
                    group.database.save()
                    return HttpResponse(status=200)
                text = text[1:].strip().lower()
                text_is_cmd = True
                if text in ('link', 'rules', 'cmds'):
                    if text == 'link':
                        if 'invite_link' in (chat_info := group.get_chat()):
                            group.send_message(
                                group.translate('join'),
                                keyboards.invite(chat_info['invite_link']),
                                message_id,
                                parse_mode='Markdown'
                            )
                        else:
                            group.send_message(group.translate('link_not_set'), reply_to_message_id=message_id)
                    elif text == 'rules':
                        if group.database.rules:
                            group.send_message(group.database.rules, reply_to_message_id=message_id,
                                               parse_mode='Markdown')
                        else:
                            group.send_message(group.translate('rules'), reply_to_message_id=message_id)
                    elif text == 'cmds':
                        if all_cmds := models.Command.objects.filter(group=group.database):
                            cmd_text = group.translate('base_cmds')
                            for cmd in all_cmds:
                                cmd_text += group.translate('cmd', cmd.cmd, cmd.get_permission_display())
                        else:
                            cmd_text = group.translate('no_cmd')
                        group.send_message(cmd_text, reply_to_message_id=message_id)
                    user.database.save()
                    group.database.save()
                    return HttpResponse(status=200)
            else:
                text_is_cmd = False
        if user_perms['status'] == 'creator' and text_is_cmd:
            if text.split()[0] in ('start', 'start@sholexbot', 'setlang', 'setcmd', 'unset'):
                if text in ('start', 'start@sholexbot'):
                    group.send_message(group.translate('group_start'), reply_to_message_id=message_id)
                elif text.startswith('setlang'):
                    if len(lang := text.split()) == 2:
                        lang = lang[1].strip().lower()
                        if lang in ['fa', 'en']:
                            group.database.lang = lang
                            group.send_message(group.translate('setlang'))
                        else:
                            group.send_message(group.translate('lang_not_found', lang))
                    else:
                        group.send_message(group.translate('cmd_invalid'), reply_to_message_id=message_id)
                elif text.startswith('setcmd'):
                    if len(
                            (splinted_text := text.split(' ')[1:])
                    ) >= 3 and splinted_text[0] in ('m', 'a', 'c') and len(splinted_text[1]) <= 50:
                        text_answer = ' '.join(splinted_text[2:]).replace(
                            '&', '&amp;'
                        ).replace('>', '&gt;').replace('<', '&lt;')
                        text_len = len(text) + 1
                        for entity in filter(lambda item: item['type'] not in (
                                'bot_command', 'mention', 'phone_number', 'hashtag', 'cashtag', 'email'
                        ), message['entities']):
                            diff = entity['offset'] - (text_len - len(text_answer))
                            target = text_answer.encode(
                                    'utf-16-le'
                                )[diff * 2:(entity['length'] + diff) * 2].decode('utf-16-le')
                            result = functions.entity(
                                entity['type'],
                                target,
                                entity.get('url', None),
                                *entity.get('url', ()),
                                entity.get('user', {}).get('id', ()),
                            )
                            text_answer = text_answer.replace(target, result)
                        cmd, created = models.Command.objects.get_or_create(
                            cmd=splinted_text[1],
                            group=group.database,
                            defaults={'permission': splinted_text[0], 'answer': text_answer},
                        )
                        if created:
                            group.send_message(
                                group.translate('command_added', splinted_text[1]),
                                reply_to_message_id=message_id,
                            )
                        else:
                            group.send_message(
                                group.translate('cmd_already', splinted_text[1]),
                                reply_to_message_id=message_id,
                            )
                    else:
                        group.send_message(group.translate('cmd_invalid'), reply_to_message_id=message_id)
                elif text.startswith('unset'):
                    if len(cmd := text.split()) == 2:
                        if len(cmd := cmd[1]) <= 50:
                            try:
                                cmd = models.Command.objects.get(group=group.database, cmd=cmd)
                            except models.Command.DoesNotExist:
                                group.send_message(group.translate('cmd_notset', cmd), reply_to_message_id=message_id)
                            else:
                                cmd.delete()
                                group.send_message(
                                    group.translate('cmd_delete', cmd.cmd),
                                    reply_to_message_id=message_id,
                                    parse_mode=''
                                )
                        else:
                            group.send_message(group.translate('cmd_invalid'), reply_to_message_id=message_id)
                    else:
                        group.send_message(group.translate('cmd_invalid'), reply_to_message_id=message_id)
                user.database.save()
                group.database.save()
                return HttpResponse(status=200)
            else:
                try:
                    command = models.Command.objects.get(group=group.database, permission__in=('m', 'a', 'c'), cmd=text)
                except models.Command.DoesNotExist:
                    pass
                else:
                    group.send_message(command.answer, reply_to_message_id=message_id, parse_mode='HTML')
                    user.database.save()
                    group.database.save()
                    return HttpResponse(status=200)
        # Admin Section
        if user_perms['status'] in ('administrator', 'creator') and text_is_cmd:
            # Restricting
            if 'reply_to_message' in message and any(word in text for word in (
                    'kick',
                    'ban',
                    'mute',
                    'unmute',
                    'warn',
                    'warnfree',
                    'clear',
                    'whitelist',
                    'unwhite',
                    'validate',
                    'unban',
                    'allow',
                    'noadd'
            )):
                if user_perms['status'] == 'creator' or user_perms['can_restrict_members']:
                    if any(text.startswith(cmd) for cmd in ('kick', 'ban')):
                        if group.get_chat_member(
                                message['reply_to_message']['from']['id']
                        )['status'] not in ('creator', 'administrator'):
                            if len(new_text := text.split()) == 3:
                                if new_text[2] in settings.DATES and new_text[1].isdigit():
                                    group.kick_chat_member(
                                        message['reply_to_message']['from']['id'],
                                        message['reply_to_message']['from']['first_name'],
                                        group.translate('admin_cmd'),
                                        (datetime.datetime.now() + datetime.timedelta(
                                            **{settings.DATES[new_text[2]]: int(new_text[1])}
                                        )).timestamp()
                                    )
                                else:
                                    group.send_message(
                                        group.translate('time_invalid'), reply_to_message_id=message_id
                                    )
                            else:
                                group.kick_chat_member(
                                    message['reply_to_message']['from']['id'],
                                    message['reply_to_message']['from']['first_name'],
                                    group.translate('admin_cmd')
                                )
                        else:
                            group.send_message(group.translate('admin_user'), reply_to_message_id=message_id)
                    elif text == 'noadd':
                        group.noadd(classes.User(message['reply_to_message']['from']['id']))
                    elif text == 'validate':
                        if (validation := models.Verify.objects.filter(
                            user=classes.User(message['reply_to_message']['from']['id']).database,
                            group=group.database,
                        )).exists():
                            validation = validation.first()
                        else:
                            validation = models.Verify.objects.create(
                                user=classes.User(message['reply_to_message']['from']['id']).database,
                                group=group.database,
                                valid_until=datetime.datetime.now()
                            )
                        if validation.validated:
                            group.send_message(group.translate('validated'), reply_to_message_id=message_id)
                        else:
                            validation.validated = True
                            validation.save()
                            group.restrict_chat_member(
                                message['reply_to_message']['from']['id'], group.get_chat()['permissions']
                            )
                            group.send_message(group.translate('admin_verified'), reply_to_message_id=message_id)
                    elif text == 'allow':
                        if group.database.number_range not in (
                                target_user := classes.User(message['reply_to_message']['from']['id'])
                        ).database.number_pass.all():
                            target_user.database.number_pass.add(group.database)
                            group.restrict_chat_member(target_user.database.chat_id, group.get_chat()['permissions'])
                            group.send_message(group.translate('allowed'), reply_to_message_id=message_id)
                        else:
                            group.send_message(group.translate('already_allowed'), reply_to_message_id=message_id)
                    elif text in ('clear', 'warnfree'):
                        group.clear(message['reply_to_message']['from'])
                    elif text == 'unban':
                        group.unban_chat_member(message['reply_to_message']['from'])
                    elif text == 'unmute':
                        if not group.get_chat_member(
                                message['reply_to_message']['from']['id']
                        ).get('can_send_messages', None):
                            group.restrict_chat_member(
                                message['reply_to_message']['from']['id'],
                                group.get_chat()['permissions']
                            )
                            group.send_message(group.translate(
                                'unmute',
                                message['reply_to_message']['from']['first_name'],
                                message['reply_to_message']['from']['id']
                            ), parse_mode='Markdown')
                        else:
                            group.send_message(group.translate('unmuted'), reply_to_message_id=message_id)
                    elif text.startswith('mute'):
                        if group.get_chat_member(
                                message['reply_to_message']['from']['id']
                        )['status'] not in ('creator', 'administrator'):
                            if len((new_text := text.split())) == 3:
                                if new_text[2] in settings.DATES and new_text[1].isdigit():
                                    group.restrict_chat_member(
                                        message['reply_to_message']['from']['id'],
                                        {'can_send_messages': False},
                                        (datetime.datetime.now() + datetime.timedelta(
                                            **{settings.DATES[new_text[2]]: int(new_text[1])}
                                        )).timestamp()
                                    )
                                    group.send_message(group.translate(
                                        'mute_time',
                                        message['reply_to_message']['from']['first_name'],
                                        message['reply_to_message']['from']['id'],
                                        new_text[1],
                                        group.translate(new_text[2])
                                    ), parse_mode='Markdown')
                            else:
                                group.restrict_chat_member(
                                    message['reply_to_message']['from']['id'],
                                    {'can_send_messages': False}
                                )
                                group.send_message(group.translate(
                                    'mute',
                                    message['reply_to_message']['from']['first_name'],
                                    message['reply_to_message']['from']['id']
                                ), parse_mode='Markdown')
                        else:
                            group.send_message(
                                group.translate('admin_user'), reply_to_message_id=message_id, parse_mode='Markdown'
                            )
                    elif text == 'warn':
                        if group.get_chat_member(
                                message['reply_to_message']['from']['id']
                        )['status'] not in ('creator', 'administrator'):
                            group.warn_user(
                                classes.User(message['reply_to_message']['from']['id']),
                                group.translate('admin_cmd'),
                                message['reply_to_message']['message_id']
                            )
                        else:
                            group.send_message(
                                group.translate('admin_user'), reply_to_message_id=message_id
                            )
                    elif text == 'whitelist':
                        if group.get_chat_member(message['reply_to_message']['from']['id'])['status'] not in (
                                'creator', 'administrator'
                        ):
                            if (target_user := classes.User(
                                    message['reply_to_message']['from']['id']
                            )).database not in group.database.white_list.all():
                                group.database.white_list.add(target_user.database)
                                group.send_message(group.translate('whitelist'), reply_to_message_id=message_id)
                            else:
                                group.send_message(group.translate('already_white'), reply_to_message_id=message_id)
                        else:
                            group.send_message(group.translate('admin_user'), reply_to_message_id=message_id)
                    elif text == 'unwhite':
                        if (target_user := classes.User(
                                message['reply_to_message']['from']['id']
                        )).database in group.database.white_list.all():
                            group.database.white_list.remove(target_user.database)
                            group.send_message(group.translate('unwhite'), reply_to_message_id=message_id)
                        else:
                            group.send_message(group.translate('not_white'), reply_to_message_id=message_id)
                else:
                    group.send_message(
                        group.translate('permission'), reply_to_message_id=message['message_id']
                    )
            # Pin
            elif text == 'pin':
                if (
                        user_perms['status'] == 'creator' or user_perms['can_pin_messages']
                ) and 'reply_to_message' in message:
                    group.pin_chat_message(message['reply_to_message']['message_id'])
                else:
                    group.send_message('You can not perform this action !', reply_to_message_id=message_id)
            # Getting User Status
            elif text == 'status' and 'reply_to_message' in message:
                if 'reply_to_message' in message:
                    group.send_message(group.translate('user_warn', group.get_warns(
                        classes.User(message['reply_to_message']['from']['id']).database
                    ).count, group.database.max_warn), reply_to_message_id=message_id)
                else:
                    group.send_message(group.translate('reply'), reply_to_message_id=message_id)
            # No reply commands
            elif any(word in text for word in (
                'lock',
                'lockdown',
                'unlock',
                'clearwhite',
                'unban',
                'warnfree',
                'clear',
                'validate',
                'unmute',
                'noadd',
                'kick'
            )):
                if user_perms['status'] == 'creator' or user_perms['can_restrict_members']:
                    if text in ('lock', 'lockdown'):
                        group.lockdown()
                        group.send_message(group.translate('lockdown'))
                    elif text == 'unlock':
                        if group.database.last_permissions:
                            group.unlock()
                            group.send_message(group.translate('unlockdown'))
                        else:
                            group.send_message(group.translate('not_locked'), reply_to_message_id=message_id)
                    elif text == 'clearwhite':
                        group.database.white_list.clear()
                        group.send_message(group.translate('clear_white'), reply_to_message_id=message_id)
                    elif len(new_text := text.split()) == 2:
                        if (result := models.User.objects.filter(username=new_text[1])).exists():
                            target_user = result.first()
                        else:
                            group.send_message(group.translate('username'), reply_to_message_id=message_id)
                            user.database.save()
                            group.database.save()
                            return HttpResponse(status=200)
                        if text.startswith('unban'):
                            group.unban_chat_member(group.get_chat_member(target_user.chat_id)['user'])
                        elif text.startswith('noadd'):
                            group.noadd(classes.User(instance=target_user.first()))
                        elif text.startswith('validate'):
                            if not (validation := models.Verify.objects.filter(
                                user=target_user,
                                group=group.database,
                            )).exists():
                                validation = models.Verify.objects.create(
                                    user=target_user, group=group.database, valid_until=datetime.datetime.now()
                                )
                            else:
                                validation = validation.first()
                            if validation.validated:
                                group.send_message(group.translate('validated'), reply_to_message_id=message_id)
                            else:
                                validation.validated = True
                                validation.save()
                                group.restrict_chat_member(
                                    target_user.chat_id, group.get_chat()['permissions']
                                )
                                group.send_message(
                                    group.translate('admin_verified'), reply_to_message_id=message_id
                                )
                        elif text.startswith('unmute'):
                            group.restrict_chat_member(
                                target_user.chat_id,
                                group.get_chat()['permissions']
                            )
                            group.send_message(
                                group.translate('unmute', new_text[1], target_user.chat_id),
                                parse_mode='Markdown'
                            )
                        elif any(text.startswith(word) for word in ('warnfree', 'clear')):
                            group.clear(group.get_chat_member(target_user.chat_id)['user'])
                        elif text.startswith('kick'):
                            group.kick_chat_member(
                                target_user.chat_id,
                                target_user.username,
                                group.translate('admin_cmd')
                            )
                else:
                    group.send_message(group.translate('permission'), reply_to_message_id=message_id)
            elif text.startswith('on') and (
                    user_perms['status'] == 'creator' or user_perms['can_restrict_members']
            ):
                if len(new_text := text.split()) > 1:
                    for lock in new_text[1:]:
                        lock_name = lock + '_lock'
                        try:
                            getattr(group.database, lock_name)
                            setattr(group.database, lock_name, True)
                        except AttributeError:
                            group.send_message(
                                group.translate('invalid_lock', lock), reply_to_message_id=message_id, parse_mode=''
                            )
                        else:
                            group.send_message(
                                group.translate('lock_on', lock.replace('_', ' ')),
                                reply_to_message_id=message_id,
                                parse_mode=''
                            )
                else:
                    group.send_message(group.translate('one_on'), reply_to_message_id=message_id)
            # Manual lock managing
            elif text.startswith('off') and (
                    user_perms['status'] == 'creator' or user_perms['can_restrict_members']
            ):
                if len(new_text := text.split()) > 1:
                    for lock in new_text[1:]:
                        try:
                            getattr(group.database, lock + '_lock')
                            setattr(group.database, lock + '_lock', False)
                        except AttributeError:
                            group.send_message(
                                group.translate('invalid_lock', lock), reply_to_message_id=message_id, parse_mode=''
                            )
                        else:
                            group.send_message(
                                group.translate('lock_off', lock.replace('_', ' ')),
                                reply_to_message_id=message_id,
                                parse_mode=''
                            )
                else:
                    group.send_message(group.translate('one_off'), reply_to_message_id=message_id)
            # Unpin
            elif text == 'unpin':
                if user_perms['status'] == 'creator' or user_perms['can_pin_messages']:
                    group.unpin_chat_message()
                else:
                    group.send_message('You can not unpin messages !', reply_to_message_id=message_id)
            # Deleting Messages
            elif any(option in text for option in ('delete', 'deleteall')) and (
                    user_perms['status'] == 'creator' or user_perms.get('can_delete_messages', False)
            ):
                if text == 'deleteall':
                    group.send_message(group.translate('delete_all'), reply_to_message_id=message_id)
                    tasks.delete_all(group.database.chat_id, user.database.chat_id)
                else:
                    if len(new_text := text.split()) == 2:
                        try:
                            delete_count = int(new_text[1]) + 1
                        except ValueError:
                            group.send_message(group.translate('cleaning_number'), reply_to_message_id=message_id)
                        else:
                            if delete_count > 60 or delete_count < 0:
                                delete_count = 60
                            for delete_message in group.get_messages(delete_count + 1)[1:]:
                                group.delete_message(delete_message.message_unique_id)
                                delete_message.delete()
                            group.send_message(group.translate('cleaning'))
                    else:
                        group.send_message(group.translate('cmd_invalid'), reply_to_message_id=message_id)
            # Leaving the group
            elif text == 'leave' and user_perms['status'] == 'creator':
                group.send_message(group.translate('leave'))
                group.leave_chat()
                group.database.status = 'd'
            # Setting link
            elif text == 'setlink':
                if user_perms['status'] == 'creator' or (
                        user_perms['status'] == 'administrator' and user_perms['can_invite_users']
                ):
                    group.export_chat_invite_link(message_id)
            # Showing filters
            elif text == 'filters':
                filter_text = group.translate('base_filter')
                for word in group.database.words.all():
                    filter_text += word.text + ' '
                group.send_message(filter_text, reply_to_message_id=message_id)
            # Unfiltering
            elif text.startswith('unfilter'):
                if len(splinted_text := text.lower().split()[1:]) >= 1:
                    problems = 0
                    for word in splinted_text:
                        if len(word) <= 50:
                            try:
                                word = group.database.words.get(text=word)
                            except models.Word.DoesNotExist:
                                group.send_message(
                                    group.translate('not_filtered', word), reply_to_message_id=message_id, parse_mode=''
                                )
                                problems += 1
                            else:
                                group.database.words.remove(word)
                        else:
                            group.send_message(
                                group.translate('word', word), reply_to_message_id=message_id, parse_mode=''
                            )
                            problems += 1
                    if problems != len(splinted_text):
                        group.send_message(group.translate('unfilter'), reply_to_message_id=message_id)
                else:
                    group.send_message(group.translate('one_word'), reply_to_message_id=message_id)
            # Filtering
            elif text.startswith('filter'):
                if len(splinted_text := text.lower().split()[1:]) >= 1:
                    problems = 0
                    for word in splinted_text:
                        if len(word) <= 50:
                            word, created = models.Word.objects.get_or_create(text=word)
                            if word not in group.database.words.all():
                                group.database.words.add(word)
                            else:
                                group.send_message(
                                    group.translate('already_filtered', word),
                                    reply_to_message_id=message_id,
                                    parse_mode=''
                                )
                                problems += 1
                        else:
                            group.send_message(
                                group.translate('not_word', word),
                                reply_to_message_id=message_id,
                                parse_mode=''
                            )
                            problems += 1
                    if problems != len(splinted_text):
                        group.send_message(group.translate('filtered'), reply_to_message_id=message_id)
                else:
                    group.send_message(
                        group.translate('one_word'), reply_to_message_id=message_id
                    )
            # Login
            elif text == 'login':
                user.send_message(
                    group.translate('login'),
                    {'inline_keyboard': [[{
                        'text': 'Login 🔐',
                        'url': f'https://bot.sholexteam.ir/groupguard/login/{group.login(user.database)}/'
                    }]]}
                )
                group.send_message(group.translate('login_sent'), user.keyboard('login'), message_id)
            elif text == 'panel':
                keyboard = keyboards.inlinePanel(message['chat']['id'], message['from']['id'])
                if user.database.lang == 'fa':
                    keyboard = keyboard['fa']
                else:
                    keyboard = keyboard['en']
                user.send_message(
                    group.translate('inline_panel'),
                    keyboard
                )
                group.send_message(group.translate('panel_sent'), reply_to_message_id=message_id)
            else:
                try:
                    command = models.Command.objects.get(
                        cmd=text, group=group.database, permission__in=('m', 'a')
                    )
                except models.Command.DoesNotExist:
                    pass
                else:
                    group.send_message(command.answer, reply_to_message_id=message_id, parse_mode='HTML')
        elif user_perms['status'] not in ('administrator', 'creator'):
            if 'caption' in message:
                text += message['caption']
            if 'entities' in message:
                entities = [entity['type'] for entity in message['entities']]
            else:
                entities = []
            if 'caption_entities' in message:
                caption_entities = [entity['type'] for entity in message['caption_entities']]
            else:
                caption_entities = []
            all_entities = entities + caption_entities
            try:
                if group.database.force_count and 'new_chat_members' in message:
                    added_count = len(tuple(filter(
                        lambda added_user: not added_user['is_bot'] and added_user['id'] != user.database.chat_id,
                        message['new_chat_members']
                    )))
                    if added_count:
                        tasks.add(group.database.chat_id, user.database.chat_id, added_count)
                if 'new_chat_members' in message:
                    if group.database.bot_lock:
                        for new_user in (added_users := tuple(filter(
                                lambda added_user: added_user['is_bot'], message['new_chat_members']
                        ))):
                            group.kick_chat_member(new_user['id'], new_user['first_name'], group.translate('bot_lock'))
                        if added_users:
                            raise classes.Violation('Adding bots')
                else:
                    if group.database.anti_tabchi:
                        if (validation := models.Verify.objects.filter(
                                user=user.database,
                                group=group.database,
                        )).exists():
                            validation = validation.first()
                        else:
                            validation = models.Verify.objects.create(
                                user=user.database,
                                group=group.database,
                                valid_until=datetime.datetime.now() + datetime.timedelta(
                                    seconds=group.database.tabchi_time
                                )
                            )
                        if not validation.validated:
                            group.restrict_chat_member(user.database.chat_id, {'can_send_messages': False})
                            group.delete_message(message_id)
                            group.send_message(
                                group.translate('verify', user_perms['user']['first_name'], user.database.chat_id),
                                keyboards.verify(validation.verify_id),
                                delete=False,
                                parse_mode='Markdown'
                            )
                    if text_is_cmd and text in ('report', 'status'):
                        if 'reply_to_message' in message:
                            if text == 'report':
                                if group.database.reporting:
                                    group.check_report(
                                        message_id, message['reply_to_message']['message_id'], user.database
                                    )
                                else:
                                    group.send_message(
                                        group.translate('no_report'),
                                        reply_to_message_id=message_id
                                    )
                        elif text == 'status':
                            group.send_message(group.translate(
                                'warn_count', group.get_warns(user.database).count, group.database.max_warn
                            ), reply_to_message_id=message_id)
                    elif text_is_cmd and (command := models.Command.objects.filter(
                            group=group.database, cmd=text, permission='m'
                    )).exists():
                        group.send_message(
                            command.first().answer, reply_to_message_id=message_id, parse_mode='HTML'
                        )
                    elif user.database in group.database.white_list.all():  # White List
                        pass
                    elif group.database.id_lock and (
                            'mention' in all_entities or
                            'text_mention' in all_entities
                    ):
                        raise classes.Violation(group.translate('id_lock'))
                    elif group.database.link_lock and (
                            'text_link' in all_entities or
                            'url' in all_entities
                    ):
                        raise classes.Violation(group.translate('link_lock'))
                    elif group.database.english_lock and any(word in text for word in ascii_letters):
                        raise classes.Violation(group.translate('english_lock'))
                    elif group.database.persian_lock and any(
                            word in text for word in "ضصثقفغعهخحجچشسیبلاتنمکگپظطزرذدئوژ"
                    ):
                        raise classes.Violation(group.translate('persian_lock'))
                    elif group.database.sharp_lock and 'hashtag' in all_entities:
                        raise classes.Violation(group.translate('sharp_lock'))
                    elif group.database.phone_number_lock and 'phone_number' in all_entities:
                        raise classes.Violation(group.translate('phone_number_lock'))
                    elif group.database.image_lock and 'photo' in message:
                        raise classes.Violation(group.translate('image_lock'))
                    elif group.database.contact_lock and 'contact' in message:
                        raise classes.Violation(group.translate('contact_lock'))
                    elif group.database.video_lock and 'video' in message:
                        raise classes.Violation(group.translate('video_lock'))
                    elif group.database.forward_lock and 'forward_date' in message:
                        raise classes.Violation(group.translate('forward_lock'))
                    elif group.database.sticker_lock and 'sticker' in message:
                        raise classes.Violation(group.translate('sticker_lock'))
                    elif group.database.location_lock and 'location' in message:
                        raise classes.Violation(group.translate('location_lock'))
                    elif group.database.voice_message_lock and 'voice' in message:
                        raise classes.Violation(group.translate('voice_message_lock'))
                    elif group.database.video_message_lock and 'video_note' in message:
                        raise classes.Violation(group.translate('video_message_lock'))
                    elif group.database.gif_lock and 'animation' in message:
                        raise classes.Violation(group.translate('gif_lock'))
                    elif group.database.document_lock and 'document' in message and 'animation' not in message:
                        raise classes.Violation(group.translate('document_lock'))
                    elif group.database.poll_lock and 'poll' in message:
                        raise classes.Violation(group.translate('poll_lock'))
                    elif group.database.game_lock and 'game' in message:
                        raise classes.Violation(group.translate('game_lock'))
                    elif group.database.inline_keyboard_lock and 'reply_markup' in message:
                        raise classes.Violation(group.translate('inline'))
                    elif group.database.text_lock and text:
                        raise classes.Violation(group.translate('text_lock'))
                    elif any(word.text in text.lower() for word in group.database.words.all()):
                        raise classes.Violation(group.translate('filter_word'))
                    else:
                        try:
                            models.Curse.objects.get(word=text)
                        except models.Curse.DoesNotExist:
                            pass
                        else:
                            raise classes.Violation(group.translate(''))
            except classes.Violation as reason:
                group.delete_message(message_id)
                if user_perms['status'] == 'member' or user_perms.get('can_send_messages', False):
                    if group.database.punish == 'w':
                        group.warn_user(user, reason, message_id)
                    elif group.database.punish == 'm':
                        group.restrict_chat_member(user.database.chat_id, {'can_send_messages': False})
                        group.send_message(
                            group.translate(
                                'mute_reason', user_perms['user']['first_name'], user.database.chat_id, reason
                            ),
                            parse_mode='Markdown'
                        )
                    elif group.database.punish == 'b':
                        group.kick_chat_member(user.database.chat_id, user_perms['user']['first_name'], reason)
        group.database.save()
        user.database.save()
    return HttpResponse(status=200)


def login(request, login_token):
    """
    This view function will be used to login .
    """
    try:
        target_login = models.Login.objects.get(login_token=login_token)
    except models.Login.DoesNotExist:
        return HttpResponse('Login token is invalid !', status=403)
    group = classes.Group(instance=target_login.group)
    if (datetime.datetime.now() - target_login.creation_date).seconds / 60 > 10:
        return HttpResponse(group.translate('login_expired'), status=403)
    request.session['user_id'] = target_login.user.chat_id
    request.session['group_id'] = target_login.group.chat_id
    request.session['login_token'] = str(target_login.login_token)
    request.session.modified = True
    target_login.ip = get_client_ip(request)[0]
    target_login.save()
    return redirect('groupguard:panel')


def panel(request):
    """
    This view function will be used as panel back-end .
    """
    if request.session.get('user_id', False):
        user = models.User.objects.get(chat_id=request.session['user_id'])
        target_group = classes.Group(
            user,
            request.session['group_id']
        )
        if request.session.get('login_token', None):
            target_login = models.Login.objects.get(login_token=request.session['login_token'])
            target_login.ip = get_client_ip(request)[0]
            target_login.save()
        user_perms = target_group.get_chat_member(user.chat_id)
        if request.method == 'GET':
            return render(
                request,
                'panel.html',
                {
                    'form': forms.Group(user_perms, target_group.database.lang, instance=target_group.database),
                    'lang': target_group.database.lang
                }
            )

        if user_perms['status'] in ('creator', 'administrator'):
            if (form := forms.Group(
                    user_perms, target_group.database.lang, data=request.POST, instance=target_group.database
            )).is_valid():
                form.save()
            return render(request, 'panel.html', {'form': form, 'lang': target_group.database.lang})
        else:
            request.session['user_id'] = False
            return HttpResponse(target_group.translate('no_admin'))
    return HttpResponse('You are not logged in !', status=403)


def logout(request):
    """
    This view function will be used to logout .
    """
    if request.session.get('user_id', None):
        group = classes.Group(models.User.objects.get(chat_id=request.session['user_id']), request.session['group_id'])
        del request.session['user_id']
        del request.session['group_id']
        del request.session['login_token']
        return HttpResponse(group.translate('logout'))
    return HttpResponse(status=400)
