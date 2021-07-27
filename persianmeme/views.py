from persianmeme import functions, classes, keyboards, models, tasks, translations
from django.http import HttpResponse
import json
from .types import ObjectType
from django.conf import settings
from django.forms import ValidationError
from django.db.models import F
from requests import Session as RequestSession


def webhook(request):
    update = json.loads(request.body.decode())
    if 'chosen_inline_result' in update:
        try:
            used_voice = models.Voice.objects.get(id=update['chosen_inline_result']['result_id'])
        except models.Voice.DoesNotExist:
            pass
        else:
            if (user := classes.User(
                request.http_session, classes.User.Mode.NORMAL, update['chosen_inline_result']['from']['id']
            )).database.use_recent_voices:
                user.add_recent_voice(used_voice)
            if used_voice.voice_type == models.Voice.Type.NORMAL:
                used_voice.usage_count = F('usage_count') + 1
                used_voice.save()
    elif 'inline_query' in update:
        query = update['inline_query']['query']
        offset = update['inline_query']['offset']
        inline_query_id = update['inline_query']['id']
        user = classes.User(request.http_session, classes.User.Mode.SEND_AD, update['inline_query']['from']['id'])
        user.upload_voice()
        if not user.database.started:
            user.database.save()
            functions.answer_inline_query(
                inline_query_id,
                str(),
                str(),
                0,
                True,
                user.translate('start_the_bot'),
                'new_user',
                request.http_session
            )
            return HttpResponse(status=200)
        user.send_ad()
        user.set_username()
        user.database.save()
        if user.database.status != 'f':
            results, next_offset = user.get_voices(query, offset)
            functions.answer_inline_query(
                inline_query_id,
                json.dumps(results),
                next_offset,
                0,
                True,
                user.translate('add_sound'),
                'suggest_voice',
                request.http_session
            )
    elif 'callback_query' in update:
        answer_query = functions.answer_callback_query(request.http_session)
        callback_query = update['callback_query']
        if callback_query['data'] == 'none':
            return HttpResponse(status=200)
        query_id = callback_query['id']
        inliner = classes.User(
            request.http_session, classes.User.Mode.SEND_AD, callback_query['from']['id']
        )
        inliner.upload_voice()
        if not inliner.database.started:
            answer_query(query_id, inliner.translate('start_to_use'), True)
            inliner.database.save()
            return HttpResponse(status=200)
        inliner.send_ad()
        callback_data = callback_query['data'].split(':')
        try:
            message = callback_query['message']
        except KeyError:
            message = None
            message_id = None
        else:
            message_id = message['message_id']
        if callback_data[0] == 'back':
            inliner.go_back()
        elif callback_data[0].endswith('page'):
            object_type = ObjectType(int(callback_data[0].removesuffix('page')))
            page = int(callback_data[1])
            if object_type is ObjectType.PLAYLIST:
                objs, prev_page, next_page = inliner.get_playlists(page)
            elif object_type is ObjectType.PLAYLIST_VOICE:
                objs, prev_page, next_page = inliner.get_playlist_voices(page)
            elif object_type is ObjectType.FAVORITE_VOICE:
                objs, prev_page, next_page = inliner.get_favorite_voices(page)
            elif object_type is ObjectType.SUGGESTED_VOICE:
                objs, prev_page, next_page = inliner.get_suggested_voices(page)
            else:
                objs, prev_page, next_page = inliner.get_private_voices(page)
            inliner.edit_message_text(
                message_id,
                functions.make_list_string(object_type, objs),
                keyboards.make_list(object_type, objs, prev_page, next_page)
            )
        elif callback_type := ObjectType.check_value(callback_data[0]):
            if callback_type is ObjectType.PLAYLIST:
                try:
                    inliner.database.current_playlist = models.Playlist.objects.get(
                        id=callback_data[1], creator=inliner.database
                    )
                except (models.Playlist.DoesNotExist, ValueError):
                    inliner.database.save()
                    return HttpResponse(status=200)
                inliner.menu_cleanup()
                inliner.database.menu_mode = inliner.database.MenuMode.USER
                inliner.database.menu = inliner.database.Menu.USER_MANAGE_PLAYLIST
                inliner.database.back_menu = 'manage_playlists'
                answer_query(query_id, translations.user_messages['managing_playlist'], False)
                inliner.send_message(translations.user_messages['manage_playlist'], keyboards.manage_playlist)
            else:
                try:
                    if callback_type is ObjectType.PRIVATE_VOICE:
                        inliner.menu_cleanup()
                        inliner.database.current_voice = inliner.get_private_voice(callback_data[1])
                        inliner.database.back_menu = 'manage_private_voices'
                        inliner.database.menu = inliner.database.Menu.USER_MANAGE_PRIVATE_VOICE
                    elif callback_type is ObjectType.FAVORITE_VOICE:
                        inliner.menu_cleanup()
                        inliner.database.current_voice = inliner.get_favorite_voice(callback_data[1])
                        inliner.database.back_menu = 'manage_favorite_voices'
                        inliner.database.menu = inliner.database.Menu.USER_MANAGE_FAVORITE_VOICE
                    elif callback_type is ObjectType.SUGGESTED_VOICE:
                        inliner.menu_cleanup()
                        inliner.database.current_voice = inliner.get_suggested_voice(callback_data[1])
                        inliner.database.back_menu = 'manage_suggestions'
                        inliner.database.menu = inliner.database.Menu.USER_MANAGE_SUGGESTION
                    else:
                        inliner.database.current_voice = inliner.database.current_playlist.voices.get(
                            id=callback_data[1]
                        )
                        inliner.menu_cleanup()
                        inliner.database.back_menu = 'manage_playlist'
                        inliner.database.menu = inliner.database.Menu.USER_MANAGE_PLAYLIST_VOICE
                except models.Voice.DoesNotExist:
                    inliner.database.save()
                    return HttpResponse(status=200)
                inliner.database.menu_mode = inliner.database.MenuMode.USER
                answer_query(query_id, translations.user_messages['managing_voice'], False)
                inliner.send_message(translations.user_messages['manage_voice'], keyboards.manage_voice)
        elif callback_data[0] in ('accept', 'deny') and message.get('voice'):
            if target_voice := functions.check_voice(message['voice']['file_unique_id']):
                if callback_data[0] == 'accept':
                    if not inliner.like_voice(target_voice):
                        answer_query(query_id, inliner.translate('vote_before'), True)
                    else:
                        answer_query(query_id, inliner.translate('voted'), False)
                else:
                    if not inliner.dislike_voice(target_voice):
                        answer_query(query_id, inliner.translate('vote_before'), True)
                    else:
                        answer_query(query_id, inliner.translate('voted'), False)
                target_voice.save()
        elif callback_data[0] in ('up', 'down'):
            try:
                voice = models.Voice.objects.get(id=callback_data[1])
            except models.Voice.DoesNotExist:
                inliner.database.save()
                return HttpResponse(status=200)
            if callback_data[0] == 'up':
                if voice.voters.filter(user_id=inliner.database.user_id).exists():
                    answer_query(query_id, inliner.translate('voted_before'), True)
                else:
                    inliner.add_voter(voice)
                    voice.votes = F('votes') + 1
                    voice.save()
                    answer_query(query_id, inliner.translate('voice_voted'), False)
            elif callback_data[0] == 'down':
                if voice.voters.filter(user_id=inliner.database.user_id).exists():
                    inliner.remove_voter(voice)
                    voice.votes = F('votes') - 1
                    voice.save()
                    answer_query(query_id, inliner.translate('took_vote_back'), False)
                else:
                    answer_query(query_id, inliner.translate('not_voted'), True)
        elif inliner.database.rank in models.BOT_ADMINS:
            if callback_data[0] in (message_options := ('read', 'ban', 'reply')):
                inliner.delete_message(message_id)
                if not (target_message := functions.get_message(callback_data[1])):
                    inliner.database.save()
                    return HttpResponse(status=200)
                user = classes.User(
                    request.http_session, classes.User.Mode.NORMAL, instance=target_message.sender
                )
                user.send_message(user.translate('checked_by_admin'))
                if callback_data[0] == message_options[0]:
                    answer_query(query_id, translations.admin_messages['read'], False)
                elif callback_data[0] == message_options[1]:
                    if user.database.rank == user.database.Rank.USER:
                        user.send_message(translations.user_messages['you_are_banned'])
                        user.database.status = user.database.Status.BANNED
                        answer_query(query_id, inliner.translate('banned', user.database.chat_id), True)
                        user.database.save()
                    else:
                        answer_query(query_id, translations.admin_messages['user_is_admin'], True)
                elif callback_data[0] == message_options[2]:
                    inliner.database.menu = inliner.database.Menu.ADMIN_MESSAGE_USER
                    inliner.database.menu_mode = inliner.database.MenuMode.ADMIN
                    inliner.menu_cleanup()
                    inliner.database.back_menu = 'chat_id'
                    inliner.database.temp_user_id = user.database.chat_id
                    inliner.send_message(translations.admin_messages['reply'], keyboards.en_back)
                    answer_query(query_id, translations.admin_messages['replying'], False)
            elif callback_data[0] in ('admin_accept', 'admin_deny'):
                if callback_data[0] == 'admin_deny':
                    if inliner.delete_semi_active(message['voice']['file_unique_id']):
                        answer_query(query_id, translations.admin_messages['deleted'], False)
                    else:
                        answer_query(query_id, translations.admin_messages['processed_before'], False)
                elif callback_data[0] == 'admin_accept':
                    if functions.accept_voice(message['voice']['file_unique_id']):
                        answer_query(query_id, translations.admin_messages['accepted'], False)
                    else:
                        answer_query(query_id, translations.admin_messages['processed_before'], False)
                inliner.delete_message(message_id)
            elif callback_data[0] in ('delete', 'delete_deny'):
                if not (target_delete := functions.get_delete(callback_data[1])):
                    return HttpResponse(status=200)
                user = classes.User(
                    request.http_session, classes.User.Mode.NORMAL, instance=target_delete.user
                )
                if callback_data[0] == 'delete':
                    target_delete.voice.delete()
                    answer_query(query_id, translations.admin_messages['deleted'], True)
                    user.send_message(user.translate('deleted'))
                elif callback_data[0] == 'delete_deny':
                    target_delete.delete()
                    answer_query(query_id, translations.admin_messages['denied'], False)
                    user.send_message(user.translate('delete_denied'))
                inliner.delete_message(message_id)
        inliner.database.save()
    else:
        if 'message' in update:
            message = update['message']
        else:
            return HttpResponse(status=200)
        text = message.get('text', None)
        message_id = message['message_id']
        if message['chat']['id'] < 0:
            return HttpResponse(status=200)
        user = classes.User(request.http_session, classes.User.Mode.SEND_AD, message['chat']['id'])
        user.set_username()
        user.send_ad()
        user.database.started = True
        if text in ('بازگشت 🔙', 'Back 🔙'):
            user.go_back()
            return HttpResponse(status=200)
        if user.database.rank != user.database.Rank.USER:
            if text == '/admin':
                user.menu_cleanup()
                user.database.menu_mode = user.database.MenuMode.ADMIN
                user.database.menu = user.database.Menu.ADMIN_MAIN
                user.send_message(user.translate('admin_panel'), keyboards.owner, message_id)
                user.database.save()
                return HttpResponse(status=200)
            elif text == '/user':
                user.menu_cleanup()
                user.database.menu_mode = user.database.MenuMode.USER
                user.database.menu = user.database.Menu.USER_MAIN
                user.send_message(user.translate('user_panel'), keyboards.user, message_id)
                user.database.save()
                return HttpResponse(status=200)
        if user.database.rank != user.database.Rank.USER and user.database.menu_mode == user.database.MenuMode.ADMIN:
            if text == '/start':
                user.menu_cleanup()
                user.start()
            elif text and text.startswith('/start') and len(splinted_text := text.split(' ')) == 2:
                if splinted_text[1] == 'suggest_voice':
                    user.menu_cleanup()
                    user.add_sound()
                elif splinted_text[1] == 'new_user':
                    user.start()
                else:
                    user.menu_cleanup()
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    try:
                        if result := user.join_playlist(splinted_text[1]):
                            user.send_message(
                                user.translate('joined_playlist', result.name), keyboards.owner
                            )
                        else:
                            user.send_message(
                                user.translate('already_joined_playlist'), keyboards.owner
                            )
                    except (models.Playlist.DoesNotExist, ValidationError):
                        user.send_message(user.translate('invalid_playlist'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_MAIN:
                user.database.back_menu = 'main'
                # All Admins Section
                if text == 'Add Sound':
                    user.add_sound()
                elif text == 'Voice Count':
                    user.send_message(functions.count_voices())
                elif text == 'Member Count':
                    user.send_message(user.translate('member_count', models.User.objects.count()))
                # Admins & Owner section
                elif user.database.rank in models.BOT_ADMINS and text in (admin_options := (
                    'Get User',
                    'Ban a User',
                    'Unban a User',
                    'Full Ban',
                    'Delete Sound',
                    'Accepted',
                    'Ban Vote',
                    'Accept Voice',
                    'Deny Voice',
                    'Get Voice',
                    'Edit Voice',
                    'File ID'
                )):
                    if text == admin_options[0]:
                        user.database.menu = user.database.Menu.ADMIN_GET_USER
                        user.send_message(user.translate('chat_id'), keyboards.en_back)
                    elif text == admin_options[1]:
                        user.database.menu = user.database.Menu.ADMIN_BAN_USER
                        user.send_message(user.translate('chat_id'), keyboards.en_back)
                    elif text == admin_options[2]:
                        user.database.menu = user.database.Menu.ADMIN_UNBAN_USER
                        user.send_message(user.translate('chat_id'), keyboards.en_back)
                    elif text == admin_options[3]:
                        user.database.menu = user.database.Menu.ADMIN_FULL_BAN_USER
                        user.send_message(user.translate('chat_id'), keyboards.en_back)
                    elif text == admin_options[4]:
                        user.database.menu = user.database.Menu.ADMIN_DELETE_VOICE
                        user.send_message(user.translate('voice'), keyboards.en_back)
                    elif text == admin_options[5]:
                        if (accepted_voices := models.Voice.objects.filter(
                                status=models.Voice.Status.SEMI_ACTIVE
                        )).exists():
                            for voice in accepted_voices:
                                user.send_voice(voice.file_id, voice.name, {'inline_keyboard': [[
                                    {'text': 'Accept', 'callback_data': 'admin_accept'},
                                    {'text': 'Deny', 'callback_data': 'admin_deny'}
                                ]]})
                            user.send_message(
                                user.translate('accepted_voices'), reply_to_message_id=message_id
                            )
                        else:
                            user.send_message(
                                user.translate('no_accepted'), reply_to_message_id=message_id
                            )
                    elif text == admin_options[6]:
                        user.database.menu = user.database.Menu.ADMIN_BAN_VOTE
                        user.send_message(user.translate('voice'), keyboards.en_back)
                    elif text == admin_options[7]:
                        user.database.menu = user.database.Menu.ADMIN_ACCEPT_VOICE
                        user.send_message(user.translate('voice'), keyboards.en_back)
                    elif text == admin_options[8]:
                        user.database.menu = user.database.Menu.ADMIN_DENY_VOICE
                        user.send_message(user.translate('voice'), keyboards.en_back)
                    elif text == admin_options[9]:
                        user.database.menu = user.database.Menu.ADMIN_GET_VOICE
                        user.send_message(
                            user.translate('send_voice_id'), keyboards.en_back
                        )
                    elif text == admin_options[10]:
                        user.database.menu = user.database.Menu.ADMIN_SEND_EDIT_VOICE
                        user.send_message(
                            user.translate('send_edit_voice'), keyboards.en_back
                        )
                    else:
                        user.database.menu = user.database.Menu.ADMIN_FILE_ID
                        user.send_message(user.translate('send_file_id'), keyboards.en_back)
                # Owner Section
                elif user.database.rank == user.database.Rank.OWNER and text in (owner_options := (
                    'Message User',
                    'Add Ad',
                    'Delete Ad',
                    'Delete Requests',
                    'Broadcast',
                    'Edit Ad',
                    'Messages'
                )):
                    if text == owner_options[0]:
                        user.database.menu = user.database.Menu.ADMIN_MESSAGE_USER_ID
                        user.send_message(user.translate('chat_id'), keyboards.en_back)
                    elif text == owner_options[1]:
                        user.database.menu = user.database.Menu.ADMIN_ADD_AD
                        user.send_message(user.translate('send_ad'), keyboards.en_back)
                    elif text == owner_options[2]:
                        user.database.menu = user.database.Menu.ADMIN_DELETE_AD
                        user.send_message(user.translate('send_ad_id'), keyboards.en_back)
                    elif text == owner_options[3]:
                        if (delete_requests := models.Delete.objects.all()).exists():
                            for delete_request in delete_requests:
                                user.send_voice(
                                    delete_request.voice.file_id,
                                    f'From : {delete_request.user.chat_id}',
                                    keyboards.delete_voice(delete_request.delete_id)
                                )
                            user.send_message(
                                user.translate('delete_requests'), reply_to_message_id=message_id
                            )
                        else:
                            user.send_message(
                                user.translate('no_delete_requests'), reply_to_message_id=message_id
                            )
                    elif text == owner_options[4]:
                        user.database.menu = user.database.Menu.ADMIN_BROADCAST
                        user.send_message(user.translate('broadcast'), keyboards.en_back)
                    elif text == owner_options[5]:
                        user.database.menu = user.database.Menu.ADMIN_EDIT_AD_ID
                        user.send_message(user.translate('edit_ad'), keyboards.en_back)
                    else:
                        user.send_messages()
                elif 'voice' in message:
                    if search_result := user.get_public_voice(message):
                        user.send_message(
                            user.translate('voice_info', search_result.name),
                            keyboards.use(search_result.id)
                        )
                else:
                    user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.ADMIN_VOICE_NAME:
                if text:
                    if user.validate_voice_name(message):
                        user.database.menu = user.database.Menu.ADMIN_VOICE_TAGS
                        user.database.temp_voice_name = text
                        user.database.back_menu = 'voice_name'
                        user.send_message(user.translate('voice_tags'))
                else:
                    user.send_message(user.translate('voice_name'))
            elif user.database.menu == user.database.Menu.ADMIN_VOICE_TAGS:
                if user.process_voice_tags(text):
                    user.database.menu = user.database.Menu.ADMIN_NEW_VOICE
                    user.database.back_menu = 'voice_tags'
                    user.send_message(user.translate('voice'))
            elif user.database.menu == user.database.Menu.ADMIN_NEW_VOICE:
                if user.voice_exists(message):
                    if user.add_voice(
                            message['voice']['file_id'],
                            message['voice']['file_unique_id'],
                            models.Voice.Status.ACTIVE
                    ):
                        user.database.menu = user.database.Menu.ADMIN_MAIN
                        user.send_message(user.translate('voice_added'), keyboards.owner)
                    else:
                        user.send_message(user.translate('voice_is_added'))
            elif user.database.menu == user.database.Menu.ADMIN_DELETE_VOICE:
                if user.voice_exists(message):
                    user.delete_voice(message['voice']['file_unique_id'])
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    user.send_message(user.translate('deleted'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_BAN_USER:
                try:
                    user_id = int(text)
                except (ValueError, TypeError):
                    user.send_message(user.translate('invalid_user_id'))
                else:
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    functions.change_user_status(user_id, models.User.Status.BANNED)
                    user.send_message(
                        user.translate('banned', user_id),
                        keyboards.owner
                    )
            elif user.database.menu == user.database.Menu.ADMIN_UNBAN_USER:
                try:
                    user_id = int(text)
                except (ValueError, TypeError):
                    user.send_message(user.translate('invalid_user_id'))
                else:
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    functions.change_user_status(user_id, models.User.Status.ACTIVE)
                    user.send_message(user.translate('unbanned'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_FULL_BAN_USER:
                try:
                    user_id = int(text)
                except (ValueError, TypeError):
                    user.send_message(user.translate('invalid_user_id'))
                else:
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    functions.change_user_status(user_id, models.User.Status.FULL_BANNED)
                    user.send_message(user.translate('banned', user_id), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_MESSAGE_USER_ID:
                try:
                    user.database.temp_user_id = int(text)
                except (ValueError, TypeError):
                    user.send_message(user.translate('invalid_user_id'))
                else:
                    user.database.menu = user.database.Menu.ADMIN_MESSAGE_USER
                    user.database.back_menu = 'chat_id'
                    user.send_message(user.translate('message'))
            elif user.database.menu == user.database.Menu.ADMIN_MESSAGE_USER:
                user.database.menu = user.database.Menu.ADMIN_MAIN
                user.copy_message(message_id, keyboards.admin_message, chat_id=user.database.temp_user_id)
                user.send_message(user.translate('sent'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_ADD_AD:
                user.database.menu = user.database.Menu.ADMIN_MAIN
                ad_id = models.Ad.objects.create(chat_id=user.database.chat_id, message_id=message_id).ad_id
                user.send_message(
                    user.translate('ad_submitted', ad_id), keyboards.owner
                )
            elif user.database.menu == user.database.Menu.ADMIN_DELETE_AD:
                try:
                    models.Ad.objects.get(ad_id=int(text)).delete()
                except (ValueError, models.Ad.DoesNotExist):
                    user.send_message(
                        user.translate('invalid_ad_id'), reply_to_message_id=message_id
                    )
                else:
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    user.send_message(user.translate('ad_deleted'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_GET_USER:
                if text:
                    try:
                        int(text)
                    except ValueError:
                        user.send_message(
                            user.translate('invalid_user_id'), reply_to_message_id=message_id
                        )
                    else:
                        user.database.menu = user.database.Menu.ADMIN_MAIN
                        user.send_message(
                            user.translate('user_profile', text),
                            keyboards.owner,
                            message_id,
                            'Markdown'
                        )
                else:
                    user.send_message(user.translate('invalid_user_id'))
            elif user.database.menu == user.database.Menu.ADMIN_BROADCAST:
                user.broadcast(message_id)
                user.database.menu = user.database.Menu.ADMIN_MAIN
                user.send_message(user.translate('broadcast_start'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_EDIT_AD_ID:
                try:
                    user.set_current_ad(text)
                except (models.Ad.DoesNotExist, ValueError):
                    user.send_message(
                        user.translate('invalid_ad_id'), reply_to_message_id=message_id
                    )
                else:
                    user.database.back_menu = 'edit_ad'
                    user.database.menu = user.database.Menu.ADMIN_EDIT_AD
                    user.send_message(user.translate('replace_ad'), keyboards.en_back)
            elif user.database.menu == user.database.Menu.ADMIN_EDIT_AD:
                user.database.menu = user.database.Menu.ADMIN_MAIN
                if user.edit_current_ad(message_id):
                    user.send_message(user.translate('ad_edited'), keyboards.owner)
                else:
                    user.send_message(user.translate('ad_deleted'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_BAN_VOTE:
                if user.voice_exists(message) and \
                        (target_voice := user.get_vote(message['voice']['file_unique_id'])):
                    functions.delete_vote_sync(target_voice.message_id, request.http_session)
                    target_voice.ban_sender()
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    user.send_message(user.translate('ban_voted'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_DENY_VOICE:
                if user.voice_exists(message) and \
                        (target_voice := user.get_vote(message['voice']['file_unique_id'])):
                    user.deny_voice(target_voice)
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    user.send_message(user.translate('admin_voice_denied'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_ACCEPT_VOICE:
                if user.voice_exists(message) and \
                        (target_voice := user.get_vote(message['voice']['file_unique_id'])):
                    user.accept_voice(target_voice)
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    user.send_message(user.translate('admin_voice_accepted'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_GET_VOICE:
                if search_result := functions.get_admin_voice(text):
                    user.send_voice(search_result.file_id, search_result.name)
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    user.send_message(
                        user.translate('requested_voice'), keyboards.owner, message_id
                    )
                else:
                    user.send_message(user.translate('voice_not_found'))
            elif user.database.menu == user.database.Menu.ADMIN_SEND_EDIT_VOICE:
                if user.voice_exists(message):
                    if target_voice := user.get_public_voice(message):
                        user.database.current_voice = target_voice
                        user.database.back_menu = 'send_edit_voice'
                        user.database.menu = user.database.Menu.ADMIN_EDIT_VOICE
                        user.send_message(user.translate('edit_voice'), keyboards.edit_voice)
            elif user.database.menu == user.database.Menu.ADMIN_EDIT_VOICE:
                if text in (edit_options := ('Edit Name', 'Edit Tags')):
                    user.database.back_menu = 'edit_voice'
                    if text == edit_options[0]:
                        user.database.menu = user.database.Menu.ADMIN_EDIT_VOICE_NAME
                        user.send_message(user.translate('edit_voice_name'), keyboards.en_back)
                    else:
                        user.database.menu = user.database.Menu.ADMIN_EDIT_VOICE_TAGS
                        user.send_message(user.translate('edit_voice_tags'), keyboards.en_back)
                else:
                    user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
            elif user.database.menu == user.database.Menu.ADMIN_EDIT_VOICE_NAME:
                if user.validate_voice_name(message):
                    user.edit_voice_name(text)
                    user.send_message(user.translate('voice_name_edited'), reply_to_message_id=message_id)
                    user.go_back()
            elif user.database.menu == user.database.Menu.ADMIN_EDIT_VOICE_TAGS:
                if user.process_voice_tags(text):
                    user.edit_voice_tags()
                    user.send_message(user.translate('voice_tags_edited'), reply_to_message_id=message_id)
                    user.go_back()
            elif user.database.menu == user.database.Menu.ADMIN_FILE_ID:
                if message.get('document'):
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    user.send_message(
                        user.translate('file_id', message['document']['file_id']),
                        keyboards.owner,
                        message_id
                    )
                else:
                    user.send_message(user.translate('no_document'), reply_to_message_id=message_id)
        elif user.database.status == user.database.Status.ACTIVE and \
                (user.database.rank == user.database.Rank.USER or
                 user.database.menu_mode == user.database.MenuMode.USER):
            if text == '/start':
                user.start()
            elif text and text.startswith('/start') and len(splinted_text := text.split(' ')) == 2:
                if splinted_text[1] == 'new_user':
                    user.start()
                elif splinted_text[1] == 'suggest_voice':
                    user.menu_cleanup()
                    user.add_sound()
                else:
                    user.menu_cleanup()
                    user.database.menu = user.database.Menu.USER_MAIN
                    try:
                        if result := user.join_playlist(splinted_text[1]):
                            user.send_message(
                                user.translate('joined_playlist', result.name), keyboards.user
                            )
                        else:
                            user.send_message(
                                user.translate('already_joined_playlist'), keyboards.user
                            )
                    except (models.Playlist.DoesNotExist, ValidationError):
                        user.send_message(user.translate('invalid_playlist'), keyboards.user)
            elif user.database.menu == user.database.Menu.USER_MAIN:
                user.database.back_menu = 'main'
                if text == 'راهنما 🔰':
                    user.database.menu = user.database.Menu.USER_HELP
                    user.send_message(
                        user.translate('help'),
                        keyboards.help_keyboard(list(json.loads(settings.MEME_HELP_MESSAGES).keys()))
                    )
                elif text == 'دیسکورد':
                    user.send_message(
                        user.translate('discord'), keyboards.discord, message_id
                    )
                elif text == 'لغو رای گیری ⏹':
                    if user.cancel_voting():
                        user.send_message(user.translate('voting_canceled'), reply_to_message_id=message_id)
                    else:
                        user.send_message(user.translate('no_voting'), reply_to_message_id=message_id)
                elif text == 'حمایت مالی 💸':
                    user.send_message(
                        user.translate('donate'), reply_to_message_id=message_id, parse_mode='Markdown'
                    )
                elif text == 'گروه عمومی':
                    user.send_message(
                        user.translate('group'), keyboards.group, message_id
                    )
                elif text == 'آخرین ویس ها 🆕':
                    user.send_ordered_voice_list(user.database.VoiceOrder.new_voice_id)
                elif text == 'ارتباط با مدیریت 📬':
                    if user.sent_message:
                        user.send_message(user.translate('pending_message'))
                    else:
                        user.database.menu = user.database.Menu.USER_CONTACT_ADMIN
                        user.send_message(user.translate('send_message'), keyboards.per_back)
                elif text == 'ویس های پیشنهادی ✔':
                    user.database.menu = user.database.Menu.USER_SUGGESTIONS
                    user.send_message(user.translate('choices'), keyboards.manage_suggestions)
                elif text == 'ویس های محبوب 👌':
                    user.send_ordered_voice_list(user.database.VoiceOrder.high_votes)
                elif text == 'پر استفاده ها ⭐':
                    user.send_ordered_voice_list(user.database.VoiceOrder.high_usage)
                elif text == 'درخواست حذف ویس ✖':
                    if user.database.deletes_user.exists():
                        user.send_message(user.translate('pending_request'))
                    else:
                        user.database.menu = user.database.Menu.USER_DELETE_REQUEST
                        user.send_message(user.translate('voice'), keyboards.per_back)
                elif text == 'ویس های شخصی 🔒':
                    user.database.menu = user.database.Menu.USER_PRIVATE_VOICES
                    user.send_message(user.translate('choices'), keyboards.manage_voice_list)
                elif text == 'علاقه مندی ها ❤️':
                    user.database.menu = user.database.Menu.USER_FAVORITE_VOICES
                    user.send_message(user.translate('choices'), keyboards.manage_voice_list)
                elif text == 'پلی لیست ▶️':
                    user.database.menu = user.database.Menu.USER_PLAYLISTS
                    user.send_message(user.translate('manage_playlists'), keyboards.manage_playlists)
                elif text == 'تنظیمات ⚙':
                    user.database.menu = user.database.Menu.USER_SETTINGS
                    user.send_message(user.translate('settings'), keyboards.settings)
                elif 'voice' in message:
                    if search_result := user.get_public_voice(message):
                        user.send_message(
                            user.translate('voice_info', search_result.name),
                            keyboards.use(search_result.id)
                        )
                else:
                    user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_CONTACT_ADMIN:
                user.database.menu = user.database.Menu.USER_MAIN
                user.contact_admin(message_id)
                user.send_message(user.translate('message_sent'), keyboards.user, message_id)
            elif user.database.menu == user.database.Menu.USER_SUGGEST_VOICE_NAME:
                if text:
                    if user.validate_voice_name(message):
                        user.database.menu = user.database.Menu.USER_SUGGEST_VOICE_TAGS
                        user.database.temp_voice_name = text
                        user.database.back_menu = 'suggest_name'
                        user.send_message(user.translate('voice_tags'))
                else:
                    user.send_message(user.translate('invalid_voice_name'))
            elif user.database.menu == user.database.Menu.USER_SETTINGS:
                if text in (settings_choices := ('مرتب سازی 🗂', 'امتیازدهی ⭐', 'ویس های اخیر ⏱')):
                    user.database.back_menu = 'settings'
                    if text == settings_choices[0]:
                        user.database.menu = user.database.Menu.USER_SORTING
                        user.send_message(user.translate('select_order'), keyboards.voice_order)
                    elif text == settings_choices[1]:
                        user.database.menu = user.database.Menu.USER_RANKING
                        user.send_message(user.translate('choose'), keyboards.toggle)
                    else:
                        user.database.menu = user.database.Menu.USER_RECENT_VOICES
                        user.send_message(user.translate('choose'), keyboards.toggle)
                else:
                    user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_SUGGEST_VOICE_TAGS:
                if user.process_voice_tags(text):
                    user.database.menu = user.database.Menu.USER_SUGGEST_VOICE
                    user.database.back_menu = 'suggest_tags'
                    user.send_message(user.translate('send_voice'))
            elif user.database.menu == user.database.Menu.USER_SUGGEST_VOICE:
                if user.voice_exists(message):
                    if target_voice := user.add_voice(
                        message['voice']['file_id'],
                        message['voice']['file_unique_id'],
                        models.Voice.Status.PENDING
                    ):
                        user.database.menu = user.database.Menu.USER_MAIN
                        target_voice.message_id = target_voice.send_voice(request.http_session)
                        tasks.check_voice(target_voice.id)
                        tasks.update_votes(target_voice.id)
                        user.send_message(
                            user.translate('suggestion_sent'),
                            keyboards.user
                        )
                        target_voice.save()
                    else:
                        user.send_message(
                            user.translate('voice_exists'), reply_to_message_id=message_id
                        )
            elif user.database.menu == user.database.Menu.USER_RANKING:
                if text in (user_rankin_options := ('روشن 🔛', 'خاموش 🔴')):
                    user.database.back_menu = 'main'
                    user.database.menu = user.database.Menu.USER_SETTINGS
                    if text == user_rankin_options[0]:
                        user.database.vote = True
                        user.send_message(user.translate('voting_on'), keyboards.settings)
                    else:
                        user.database.vote = False
                        user.send_message(user.translate('voting_off'), keyboards.settings)
                else:
                    user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_SORTING:
                if text in (sorting_options := (
                    'جدید به قدیم',
                    'قدیم به جدید',
                    'بهترین به بدترین',
                    'بدترین به بهترین',
                    'پر استفاده به کم استفاده',
                    'کم استفاده به پر استفاده'
                )):
                    if text == sorting_options[0]:
                        user.database.voice_order = user.database.VoiceOrder.new_voice_id
                    elif text == sorting_options[1]:
                        user.database.voice_order = user.database.VoiceOrder.voice_id
                    elif text == sorting_options[2]:
                        user.database.voice_order = user.database.VoiceOrder.high_votes
                    elif text == sorting_options[3]:
                        user.database.voice_order = user.database.VoiceOrder.votes
                    elif text == sorting_options[4]:
                        user.database.voice_order = user.database.VoiceOrder.high_usage
                    else:
                        user.database.voice_order = user.database.VoiceOrder.low_usage
                    user.database.back_menu = 'main'
                    user.database.menu = user.database.Menu.USER_SETTINGS
                    user.send_message(user.translate('ordering_changed'), keyboards.settings)
                else:
                    user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_RECENT_VOICES:
                if text in (recent_voices_options := ('روشن 🔛', 'خاموش 🔴')):
                    user.database.back_menu = 'main'
                    user.database.menu = user.database.Menu.USER_SETTINGS
                    if text == recent_voices_options[0]:
                        user.database.use_recent_voices = True
                        user.send_message(user.translate('recent_voices_on'), keyboards.settings)
                    else:
                        user.database.use_recent_voices = False
                        user.clear_recent_voices()
                        user.send_message(user.translate('recent_voices_off'), keyboards.settings)
                else:
                    user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_DELETE_REQUEST:
                if user.voice_exists(message):
                    if target_voice := user.get_public_voice(message):
                        owner = classes.User(
                            request.http_session, classes.User.Mode.NORMAL, instance=models.User.objects.get(rank='o')
                        )
                        user.database.menu = user.database.Menu.USER_MAIN
                        user.send_message(
                            user.translate('request_created'), keyboards.user, message_id
                        )
                        user.delete_request(target_voice)
                        owner.send_message('New delete request 🗑')
            elif user.database.menu == user.database.Menu.USER_PRIVATE_VOICES:
                if text == 'افزودن ویس ⏬':
                    if user.private_voices_count <= 120:
                        user.database.menu = user.database.Menu.USER_PRIVATE_VOICE_NAME
                        user.database.back_menu = 'manage_private_voices'
                        user.send_message(user.translate('voice_name'), keyboards.per_back)
                    else:
                        user.send_message(user.translate('voice_limit'))
                elif text == 'مشاهده ی ویس ها 📝':
                    voices, prev_page, next_page = user.get_private_voices(1)
                    if voices:
                        user.send_message(
                            functions.make_list_string(ObjectType.PRIVATE_VOICE, voices),
                            keyboards.make_list(ObjectType.PRIVATE_VOICE, voices, prev_page, next_page)
                        )
                    else:
                        user.send_message(
                            user.translate('empty_private_voices'), reply_to_message_id=message_id
                        )
                else:
                    user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_PRIVATE_VOICE_NAME:
                if text:
                    if user.validate_voice_name(message):
                        user.database.temp_voice_name = text
                        user.database.menu = user.database.Menu.USER_PRIVATE_VOICE_TAGS
                        user.database.back_menu = 'private_name'
                        user.send_message(user.translate('voice_tags'))
                else:
                    user.send_message(user.translate('invalid_voice_name'))
            elif user.database.menu == user.database.Menu.USER_PRIVATE_VOICE_TAGS:
                if user.process_voice_tags(text):
                    user.database.menu = user.database.Menu.USER_PRIVATE_VOICE
                    user.database.back_menu = 'private_voice_tags'
                    user.send_message(user.translate('send_voice'))
            elif user.database.menu == user.database.Menu.USER_PRIVATE_VOICE:
                if user.voice_exists(message):
                    if user.create_private_voice(message):
                        user.database.menu = user.database.Menu.USER_PRIVATE_VOICES
                        user.database.back_menu = 'main'
                        user.send_message(user.translate('private_voice_added'), keyboards.manage_voice_list)
                    else:
                        user.send_message(user.translate('voice_exists'))
            elif user.database.menu == user.database.Menu.USER_MANAGE_PRIVATE_VOICE:
                if user.check_current_voice():
                    if text == 'حذف ویس ❌':
                        if user.delete_private_voice():
                            user.send_message(user.translate('voice_deleted'))
                        else:
                            user.send_message(user.translate('voice_deleted_before'))
                        user.go_back()
                    elif text == 'گوش دادن به ویس 🎧':
                        current_voice = user.database.current_voice
                        user.send_voice(current_voice.file_id, current_voice.name)
                    else:
                        user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_FAVORITE_VOICES:
                if text == 'افزودن ویس ⏬':
                    if user.private_voices_count <= 120:
                        user.database.menu = user.database.Menu.USER_FAVORITE_VOICE
                        user.database.back_menu = 'manage_favorite_voices'
                        user.send_message(user.translate('send_voice'), keyboards.per_back)
                    else:
                        user.send_message(user.translate('voice_limit'))
                elif text == 'مشاهده ی ویس ها 📝':
                    voices, prev_page, next_page = user.get_favorite_voices(1)
                    if voices:
                        user.send_message(
                            functions.make_list_string(ObjectType.FAVORITE_VOICE, voices),
                            keyboards.make_list(ObjectType.FAVORITE_VOICE, voices, prev_page, next_page)
                        )
                    else:
                        user.send_message(
                            user.translate('empty_favorite_voices'), reply_to_message_id=message_id
                        )
                else:
                    user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_FAVORITE_VOICE:
                if user.voice_exists(message):
                    if current_voice := user.get_public_voice(message):
                        if user.add_favorite_voice(current_voice):
                            user.database.menu = user.database.Menu.USER_FAVORITE_VOICES
                            user.database.back_menu = 'main'
                            user.send_message(
                                user.translate('added_to_favorite'),
                                keyboards.manage_voice_list
                            )
                        else:
                            user.send_message(user.translate('voice_exists_in_list'))
            elif user.database.menu == user.database.Menu.USER_MANAGE_FAVORITE_VOICE:
                if user.check_current_voice():
                    if text == 'حذف ویس ❌':
                        if user.delete_favorite_voice():
                            user.send_message(user.translate('deleted_from_list'))
                        else:
                            user.send_message(user.translate('voice_deleted_from_list_before'))
                        user.go_back()
                    elif text == 'گوش دادن به ویس 🎧':
                        current_voice = user.database.current_voice
                        user.send_voice(current_voice.file_id, current_voice.name)
                    else:
                        user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_PLAYLISTS:
                if text == 'ایجاد پلی لیست 🆕':
                    user.database.back_menu = 'manage_playlists'
                    user.database.menu = user.database.Menu.USER_CREATE_PLAYLIST
                    user.send_message(user.translate('playlist_name'), keyboards.per_back)
                elif text == 'مشاهده پلی لیست ها 📝':
                    current_page, prev_page, next_page = user.get_playlists(1)
                    if current_page:
                        user.send_message(
                            functions.make_list_string(ObjectType.PLAYLIST, current_page),
                            keyboards.make_list(keyboards.ObjectType.PLAYLIST, current_page, prev_page, next_page)
                        )
                    else:
                        user.send_message(
                            user.translate('no_playlist'), reply_to_message_id=message_id
                        )
                else:
                    user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_CREATE_PLAYLIST:
                if text and len(text) <= 60:
                    user.send_message(
                        user.translate('playlist_created', (user.create_playlist(text)).get_link())
                    )
                    user.go_back()
                else:
                    user.send_message(
                        user.translate('invalid_playlist_name'), reply_to_message_id=message_id
                    )
            elif user.database.menu == user.database.Menu.USER_MANAGE_PLAYLIST:
                if text == 'افزودن ویس ⏬':
                    user.database.menu = user.database.Menu.USER_ADD_VOICE_PLAYLIST
                    user.database.back_menu = 'manage_playlist'
                    user.send_message(user.translate('send_private_voice'), keyboards.per_back)
                elif text == 'حذف پلی لیست ❌':
                    user.delete_playlist()
                    user.send_message(
                        user.translate('playlist_deleted'), reply_to_message_id=message_id
                    )
                    user.go_back()
                elif text == 'مشاهده ی ویس ها 📝':
                    voices, prev_page, next_page = user.get_playlist_voices(1)
                    if voices:
                        user.send_message(
                            functions.make_list_string(ObjectType.PLAYLIST_VOICE, voices),
                            keyboards.make_list(ObjectType.PLAYLIST_VOICE, voices, prev_page, next_page)
                        )
                    else:
                        user.send_message(
                            user.translate('empty_playlist'), reply_to_message_id=message_id
                        )
                elif text == 'لینک دعوت 🔗':
                    user.send_message(user.translate(
                        'playlist_link',
                        user.database.current_playlist.name,
                        user.database.current_playlist.get_link()
                    ))
                elif text == 'مشترکین پلی لیست 👥':
                    user.send_message(user.translate(
                        'playlist_users_count', user.database.current_playlist.user_playlist.count()
                    ))
                else:
                    user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_ADD_VOICE_PLAYLIST:
                if user.voice_exists(message):
                    if user.add_voice_to_playlist(message['voice']['file_unique_id']):
                        user.send_message(user.translate('added_to_playlist'))
                        user.go_back()
                    else:
                        user.send_message(
                            user.translate('voice_is_not_yours'), reply_to_message_id=message_id
                        )
            elif user.database.menu == user.database.Menu.USER_MANAGE_PLAYLIST_VOICE:
                if user.check_current_voice():
                    if text == 'حذف ویس ❌':
                        if user.remove_voice_from_playlist():
                            user.send_message(user.translate('deleted_from_playlist'))
                        else:
                            user.send_message(user.translate('not_in_playlist'))
                        user.go_back()
                    elif text == 'گوش دادن به ویس 🎧':
                        current_voice = user.database.current_voice
                        user.send_voice(current_voice.file_id, current_voice.name)
                    else:
                        user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_HELP:
                help_messages = json.loads(settings.MEME_HELP_MESSAGES)
                if text in help_messages:
                    user.send_animation(**help_messages[text], reply_to_message_id=message_id)
                else:
                    user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_SUGGESTIONS:
                if text == 'پیشنهاد ویس 🔥':
                    user.add_sound()
                elif text == 'مشاهده ی ویس ها 📝':
                    voices, prev_page, next_page = user.get_suggested_voices(1)
                    if voices:
                        user.send_message(
                            functions.make_list_string(ObjectType.SUGGESTED_VOICE, voices),
                            keyboards.make_list(ObjectType.SUGGESTED_VOICE, voices, prev_page, next_page)
                        )
                    else:
                        user.send_message(
                            user.translate('empty_suggested_voices'), reply_to_message_id=message_id
                        )
                else:
                    user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_MANAGE_SUGGESTION:
                if user.check_current_voice():
                    if text == 'حذف ویس ❌':
                        if user.delete_suggested_voice():
                            user.send_message(user.translate('voice_deleted'))
                        else:
                            user.send_message(user.translate('voice_is_not_yours'))
                        user.go_back()
                    elif text == 'گوش دادن به ویس 🎧':
                        user.send_voice(user.database.current_voice.file_id, user.database.current_voice.name)
                    else:
                        user.send_message(user.translate('unknown_command'))
        user.database.save()
    return HttpResponse(status=200)


def webhook_wrapper(request):
    request.http_session = RequestSession()
    return webhook(request)
