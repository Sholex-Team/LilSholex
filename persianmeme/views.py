from persianmeme import functions, classes, keyboards, models, tasks, translations
from django.http import HttpResponse
import json
from .types import ObjectType
from django.conf import settings
from django.forms import ValidationError
from django.db.models import F
from requests import Session as RequestSession
from django.core.cache import cache
from time import time


def webhook(request):
    update = json.loads(request.body.decode())
    match update:
        case {'chosen_inline_result': chat_id_result}:
            user_chat_id = chat_id_result['from']['id']
        case {'inline_query': chat_id_result}:
            user_chat_id = chat_id_result['from']['id']
        case {'callback_query': chat_id_result}:
            user_chat_id = chat_id_result['from']['id']
        case {'message': chat_id_result}:
            if (user_chat_id := chat_id_result['chat']['id']) < 0:
                return HttpResponse(status=200)
    now = time()
    if (cache_value := cache.get_or_set(user_chat_id, (
            now + settings.SPAM_TIME, 0
    ), settings.SPAM_TIME)) == models.User.Status.BANNED:
        return HttpResponse(status=200)
    if cache_value[0] > now:
        if cache_value[1] > settings.SPAM_COUNT:
            cache.set(user_chat_id, models.User.Status.BANNED, settings.SPAM_PENALTY)
            return HttpResponse(status=200)
        cache.set(user_chat_id, (cache_value[0], cache_value[1] + 1), cache_value[0] - now)
    match update:
        case {'chosen_inline_result': chosen_inline_result}:
            try:
                used_voice = models.Voice.objects.get(id=chosen_inline_result['result_id'])
            except models.Voice.DoesNotExist:
                pass
            else:
                if (user := classes.User(
                    request.http_session, classes.User.Mode.NORMAL, user_chat_id
                )).database.use_recent_voices:
                    user.add_recent_voice(used_voice)
                if used_voice.voice_type == models.Voice.Type.NORMAL:
                    used_voice.usage_count = F('usage_count') + 1
                    used_voice.save()
        case {'inline_query': inline_query}:
            query = inline_query['query']
            offset = inline_query['offset']
            inline_query_id = inline_query['id']
            user = classes.User(request.http_session, classes.User.Mode.SEND_AD, user_chat_id)
            user.upload_voice()
            if not user.database.started:
                user.database.save()
                functions.answer_inline_query(
                    inline_query_id,
                    str(),
                    str(),
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
                    user.translate('add_sound'),
                    'suggest_voice',
                    request.http_session
                )
        case {'callback_query': callback_query}:
            answer_query = functions.answer_callback_query(request.http_session)
            if callback_query['data'] == 'none':
                return HttpResponse(status=200)
            query_id = callback_query['id']
            inliner = classes.User(request.http_session, classes.User.Mode.SEND_AD, user_chat_id)
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
                message_id = None
            else:
                message_id = message['message_id']
            match callback_data:
                case ('back',):
                    inliner.go_back()
                case (('a' | 'd' | 're') as vote_option, voice_id):
                    try:
                        target_voice = models.Voice.objects.get(id=voice_id)
                    except models.Voice.DoesNotExist:
                        return HttpResponse(status=200)
                    match vote_option:
                        case 'a':
                            if not inliner.like_voice(target_voice):
                                answer_query(query_id, inliner.translate('vote_before'), True)
                            else:
                                answer_query(query_id, inliner.translate('voted'), False)
                        case 'd':
                            if not inliner.dislike_voice(target_voice):
                                answer_query(query_id, inliner.translate('vote_before'), True)
                            else:
                                answer_query(query_id, inliner.translate('voted'), False)
                        case _:
                            answer_query(query_id, inliner.translate(
                                'voting_results', target_voice.accept_vote.count(), target_voice.deny_vote.count()
                            ), True, 180)
                case (('up' | 'down') as rate_option, voice_id):
                    try:
                        voice = models.Voice.objects.get(id=voice_id)
                    except (models.Voice.DoesNotExist, ValueError):
                        inliner.database.save()
                        return HttpResponse(status=200)
                    if rate_option == 'up':
                        if voice.voters.filter(user_id=inliner.database.user_id).exists():
                            answer_query(query_id, inliner.translate('voted_before'), True)
                        else:
                            inliner.add_voter(voice)
                            voice.votes = F('votes') + 1
                            voice.save()
                            answer_query(query_id, inliner.translate('voice_voted'), False)
                    else:
                        if voice.voters.filter(user_id=inliner.database.user_id).exists():
                            inliner.remove_voter(voice)
                            voice.votes = F('votes') - 1
                            voice.save()
                            answer_query(query_id, inliner.translate('took_vote_back'), False)
                        else:
                            answer_query(query_id, inliner.translate('not_voted'), True)
                case (ObjectType.PLAYLIST.value, playlist_id):
                    try:
                        inliner.database.current_playlist = models.Playlist.objects.get(
                            id=playlist_id, creator=inliner.database
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
                case ((
                    ObjectType.PRIVATE_VOICE.value |
                    ObjectType.FAVORITE_VOICE.value |
                    ObjectType.SUGGESTED_VOICE.value |
                    ObjectType.PLAYLIST_VOICE.value
                ) as callback_type, voice_id):
                    try:
                        match callback_type:
                            case ObjectType.PRIVATE_VOICE.value:
                                inliner.menu_cleanup()
                                inliner.database.current_voice = inliner.get_private_voice(voice_id)
                                inliner.database.back_menu = 'manage_private_voices'
                                inliner.database.menu = inliner.database.Menu.USER_MANAGE_PRIVATE_VOICE
                            case ObjectType.FAVORITE_VOICE.value:
                                inliner.menu_cleanup()
                                inliner.database.current_voice = inliner.get_favorite_voice(voice_id)
                                inliner.database.back_menu = 'manage_favorite_voices'
                                inliner.database.menu = inliner.database.Menu.USER_MANAGE_FAVORITE_VOICE
                            case ObjectType.SUGGESTED_VOICE.value:
                                inliner.menu_cleanup()
                                inliner.database.current_voice = inliner.get_suggested_voice(voice_id)
                                inliner.database.back_menu = 'manage_suggestions'
                                inliner.database.menu = inliner.database.Menu.USER_MANAGE_SUGGESTION
                            case ObjectType.PLAYLIST_VOICE.value:
                                inliner.database.current_voice = inliner.database.current_playlist.voices.get(
                                    id=voice_id
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
                case (page_type, page_str) if page_type.endswith('page'):
                    object_type = ObjectType(page_type.removesuffix('page'))
                    page = int(page_str)
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
                case (command, target_id) if inliner.database.rank == inliner.database.Rank.OWNER:
                    match command:
                        case 'read' | 'ban' | 'reply':
                            inliner.delete_message(message_id)
                            if not (target_message := functions.get_message(target_id)):
                                inliner.database.save()
                                return HttpResponse(status=200)
                            user = classes.User(
                                request.http_session, classes.User.Mode.NORMAL, instance=target_message.sender
                            )
                            user.send_message(user.translate('checked_by_admin'))
                            match command:
                                case 'read':
                                    answer_query(query_id, translations.admin_messages['read'], False)
                                case 'ban' if user.database.rank == user.database.Rank.USER:
                                    user.database.status = user.database.Status.BANNED
                                    answer_query(query_id, inliner.translate('banned', user.database.chat_id), True)
                                    user.database.save()
                                case 'reply':
                                    inliner.database.menu = inliner.database.Menu.ADMIN_MESSAGE_USER
                                    inliner.database.menu_mode = inliner.database.MenuMode.ADMIN
                                    inliner.menu_cleanup()
                                    inliner.database.back_menu = 'chat_id'
                                    inliner.database.temp_user_id = user.database.chat_id
                                    inliner.send_message(translations.admin_messages['reply'], keyboards.en_back)
                                    answer_query(query_id, translations.admin_messages['replying'], False)
                        case 'delete' | 'delete_deny':
                            if not (target_delete := functions.get_delete(target_id)):
                                return HttpResponse(status=200)
                            user = classes.User(
                                request.http_session, classes.User.Mode.NORMAL, instance=target_delete.user
                            )
                            if command == 'delete':
                                target_delete.voice.delete()
                                answer_query(query_id, translations.admin_messages['deleted'], True)
                                user.send_message(user.translate('deleted'))
                            else:
                                target_delete.delete()
                                answer_query(query_id, translations.admin_messages['denied'], False)
                                user.send_message(user.translate('delete_denied'))
                            inliner.delete_message(message_id)
                        case 'r' | 'rd':
                            try:
                                deleted_voice = models.Voice.objects.get(
                                    id=target_id, status=models.Voice.Status.DELETED
                                )
                            except models.Voice.DoesNotExist:
                                return HttpResponse(status=200)
                            user = classes.User(request.http_session, classes.User.Mode.NORMAL,
                                                instance=deleted_voice.sender)
                            if command == 'r':
                                deleted_voice.status = deleted_voice.Status.ACTIVE
                                deleted_voice.save()
                                answer_query(query_id, translations.admin_messages['voice_recovered'], True)
                                functions.edit_message_reply_markup(
                                    settings.MEME_LOGS, keyboards.recovered, message_id=message_id,
                                    session=request.http_session
                                )
                            else:
                                deleted_voice.delete()
                                user.send_message(
                                    translations.user_messages['deleted_by_admins'].format(deleted_voice.name))
                                functions.edit_message_reply_markup(
                                    settings.MEME_LOGS, keyboards.deleted, message_id=message_id,
                                    session=request.http_session
                                )
            inliner.database.save()
        case {'message': message}:
            text = message.get('text', None)
            message_id = message['message_id']
            user = classes.User(request.http_session, classes.User.Mode.SEND_AD, user_chat_id)
            user.set_username()
            user.send_ad()
            user.database.started = True
            if text in ('بازگشت 🔙', 'Back 🔙'):
                user.go_back()
                return HttpResponse(status=200)
            match user.database:
                case models.User(rank=(user.database.Rank.OWNER | user.database.Rank.ADMIN)) if text in (
                    switch_options := ('/admin', '/user')
                ):
                    if text == switch_options[0]:
                        user.menu_cleanup()
                        user.database.menu_mode = user.database.MenuMode.ADMIN
                        user.database.menu = user.database.Menu.ADMIN_MAIN
                        user.send_message(user.translate('admin_panel'), keyboards.owner, message_id)
                        user.database.save()
                        return HttpResponse(status=200)
                    else:
                        user.menu_cleanup()
                        user.database.menu_mode = user.database.MenuMode.USER
                        user.database.menu = user.database.Menu.USER_MAIN
                        user.send_message(user.translate('user_panel'), keyboards.user, message_id)
                        user.database.save()
                        return HttpResponse(status=200)
                case _ if text and text.startswith('/start'):
                    match text.split():
                        case ('/start',):
                            user.menu_cleanup()
                            user.start()
                        case ('/start', 'suggest_voice'):
                            user.menu_cleanup()
                            user.add_sound()
                        case ('/start', 'new_user'):
                            user.start()
                        case ('/start', playlist_id):
                            user.menu_cleanup()
                            user.database.menu = user.database.Menu.ADMIN_MAIN
                            target_keyboard = keyboards.owner \
                                if user.database.rank != models.User.Rank.USER or\
                                user.database.menu_mode == models.User.MenuMode.ADMIN else keyboards.user
                            try:
                                if result := user.join_playlist(playlist_id):
                                    user.send_message(
                                        user.translate('joined_playlist', result.name), target_keyboard
                                    )
                                else:
                                    user.send_message(
                                        user.translate('already_joined_playlist'), target_keyboard
                                    )
                            except (models.Playlist.DoesNotExist, ValidationError):
                                user.send_message(user.translate('invalid_playlist'), target_keyboard)
                        case _:
                            user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
                case models.User(
                    rank=(user.database.Rank.OWNER | user.database.Rank.ADMIN), menu_mode=user.database.MenuMode.ADMIN
                ):
                    match user.database.menu:
                        case user.database.Menu.ADMIN_MAIN:
                            user.database.back_menu = 'main'
                            # All Admins Section
                            not_matched = False
                            match text:
                                case 'Add Sound':
                                    user.add_sound()
                                case 'Voice Count':
                                    user.send_message(functions.count_voices())
                                case 'Member Count':
                                    user.send_message(user.translate('member_count', models.User.objects.count()))
                                case _ if 'voice' in message and (search_result := user.get_public_voice(message)):
                                    user.send_message(
                                        user.translate('voice_info', search_result.name),
                                        keyboards.use(search_result.id)
                                    )
                                case _:
                                    not_matched = True
                            if not_matched and user.database.rank in models.BOT_ADMINS:
                                match text:
                                    case 'Get User':
                                        user.database.menu = user.database.Menu.ADMIN_GET_USER
                                        user.send_message(user.translate('chat_id'), keyboards.en_back)
                                    case 'Ban a User':
                                        user.database.menu = user.database.Menu.ADMIN_BAN_USER
                                        user.send_message(user.translate('chat_id'), keyboards.en_back)
                                    case 'Unban a User':
                                        user.database.menu = user.database.Menu.ADMIN_UNBAN_USER
                                        user.send_message(user.translate('chat_id'), keyboards.en_back)
                                    case 'Full Ban':
                                        user.database.menu = user.database.Menu.ADMIN_FULL_BAN_USER
                                        user.send_message(user.translate('chat_id'), keyboards.en_back)
                                    case 'Delete Sound':
                                        user.database.menu = user.database.Menu.ADMIN_DELETE_VOICE
                                        user.send_message(user.translate('voice'), keyboards.en_back)
                                    case 'Ban Vote':
                                        user.database.menu = user.database.Menu.ADMIN_BAN_VOTE
                                        user.send_message(user.translate('voice'), keyboards.en_back)
                                    case 'Accept Voice':
                                        user.database.menu = user.database.Menu.ADMIN_ACCEPT_VOICE
                                        user.send_message(user.translate('voice'), keyboards.en_back)
                                    case 'Deny Voice':
                                        user.database.menu = user.database.Menu.ADMIN_DENY_VOICE
                                        user.send_message(user.translate('voice'), keyboards.en_back)
                                    case 'Get Voice':
                                        user.database.menu = user.database.Menu.ADMIN_GET_VOICE
                                        user.send_message(
                                            user.translate('send_voice_id'), keyboards.en_back
                                        )
                                    case 'Edit Voice':
                                        user.database.menu = user.database.Menu.ADMIN_SEND_EDIT_VOICE
                                        user.send_message(
                                            user.translate('send_edit_voice'), keyboards.en_back
                                        )
                                    case 'File ID':
                                        user.database.menu = user.database.Menu.ADMIN_FILE_ID
                                        user.send_message(user.translate('send_file_id'), keyboards.en_back)
                                    case ('Voice Review') if user.assign_voice():
                                        user.database.menu = user.database.Menu.ADMIN_VOICE_REVIEW
                                    case _ if user.database.rank == user.database.Rank.OWNER:
                                        match text:
                                            case 'Message User':
                                                user.database.menu = user.database.Menu.ADMIN_MESSAGE_USER_ID
                                                user.send_message(user.translate('chat_id'), keyboards.en_back)
                                            case 'Add Ad':
                                                user.database.menu = user.database.Menu.ADMIN_ADD_AD
                                                user.send_message(user.translate('send_ad'), keyboards.en_back)
                                            case 'Delete Ad':
                                                user.database.menu = user.database.Menu.ADMIN_DELETE_AD
                                                user.send_message(user.translate('send_ad_id'), keyboards.en_back)
                                            case 'Delete Requests':
                                                if (delete_requests := models.Delete.objects.all()).exists():
                                                    for delete_request in delete_requests:
                                                        user.send_voice(
                                                            delete_request.voice.file_id,
                                                            f'From : {delete_request.user.chat_id}',
                                                            keyboards.delete_voice(delete_request.delete_id)
                                                        )
                                                    user.send_message(
                                                        user.translate('delete_requests'),
                                                        reply_to_message_id=message_id
                                                    )
                                                else:
                                                    user.send_message(
                                                        user.translate('no_delete_requests'),
                                                        reply_to_message_id=message_id
                                                    )
                                            case 'Broadcast':
                                                user.database.menu = user.database.Menu.ADMIN_BROADCAST
                                                user.send_message(user.translate('broadcast'), keyboards.en_back)
                                            case 'Edit Ad':
                                                user.database.menu = user.database.Menu.ADMIN_EDIT_AD_ID
                                                user.send_message(user.translate('edit_ad'), keyboards.en_back)
                                            case 'Messages':
                                                user.send_messages()
                                            case 'Started Count':
                                                user.send_message(user.translate(
                                                    'started_count',
                                                    models.User.objects.filter(
                                                        started=True, status=models.User.Status.ACTIVE
                                                    ).count()
                                                ), reply_to_message_id=message_id)
                                            case 'Broadcast Status':
                                                user.database.menu = user.database.Menu.ADMIN_BROADCAST_STATUS
                                                user.send_message(user.translate('broadcast_id'), keyboards.en_back)
                        case user.database.Menu.ADMIN_VOICE_NAME:
                            if text:
                                if user.validate_voice_name(message):
                                    user.database.menu = user.database.Menu.ADMIN_VOICE_TAGS
                                    user.database.temp_voice_name = text
                                    user.database.back_menu = 'voice_name'
                                    user.send_message(user.translate('voice_tags'))
                            else:
                                user.send_message(user.translate('voice_name'))
                        case user.database.Menu.ADMIN_VOICE_TAGS:
                            if user.process_voice_tags(text):
                                user.database.menu = user.database.Menu.ADMIN_NEW_VOICE
                                user.database.back_menu = 'voice_tags'
                                user.send_message(user.translate('voice'))
                        case user.database.Menu.ADMIN_NEW_VOICE:
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
                        case user.database.Menu.ADMIN_DELETE_VOICE:
                            if user.voice_exists(message):
                                user.delete_voice(message['voice']['file_unique_id'])
                                user.database.menu = user.database.Menu.ADMIN_MAIN
                                user.send_message(user.translate('deleted'), keyboards.owner)
                        case user.database.Menu.ADMIN_BAN_USER:
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
                        case user.database.Menu.ADMIN_UNBAN_USER:
                            try:
                                user_id = int(text)
                            except (ValueError, TypeError):
                                user.send_message(user.translate('invalid_user_id'))
                            else:
                                user.database.menu = user.database.Menu.ADMIN_MAIN
                                functions.change_user_status(user_id, models.User.Status.ACTIVE)
                                user.send_message(user.translate('unbanned'), keyboards.owner)
                        case user.database.Menu.ADMIN_FULL_BAN_USER:
                            try:
                                user_id = int(text)
                            except (ValueError, TypeError):
                                user.send_message(user.translate('invalid_user_id'))
                            else:
                                user.database.menu = user.database.Menu.ADMIN_MAIN
                                functions.change_user_status(user_id, models.User.Status.FULL_BANNED)
                                user.send_message(user.translate('banned', user_id), keyboards.owner)
                        case user.database.Menu.ADMIN_MESSAGE_USER_ID:
                            try:
                                user.database.temp_user_id = int(text)
                            except (ValueError, TypeError):
                                user.send_message(user.translate('invalid_user_id'))
                            else:
                                user.database.menu = user.database.Menu.ADMIN_MESSAGE_USER
                                user.database.back_menu = 'chat_id'
                                user.send_message(user.translate('message'))
                        case user.database.Menu.ADMIN_MESSAGE_USER:
                            user.database.menu = user.database.Menu.ADMIN_MAIN
                            user.copy_message(message_id, keyboards.admin_message, chat_id=user.database.temp_user_id)
                            user.send_message(user.translate('sent'), keyboards.owner)
                        case user.database.Menu.ADMIN_ADD_AD:
                            user.database.menu = user.database.Menu.ADMIN_MAIN
                            ad_id = models.Ad.objects.create(chat_id=user.database.chat_id, message_id=message_id).ad_id
                            user.send_message(
                                user.translate('ad_submitted', ad_id), keyboards.owner
                            )
                        case user.database.Menu.ADMIN_DELETE_AD:
                            try:
                                models.Ad.objects.get(ad_id=int(text)).delete()
                            except (ValueError, models.Ad.DoesNotExist):
                                user.send_message(
                                    user.translate('invalid_ad_id'), reply_to_message_id=message_id
                                )
                            else:
                                user.database.menu = user.database.Menu.ADMIN_MAIN
                                user.send_message(user.translate('ad_deleted'), keyboards.owner)
                        case user.database.Menu.ADMIN_GET_USER:
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
                        case user.database.Menu.ADMIN_BROADCAST:
                            user.database.menu = user.database.Menu.ADMIN_MAIN
                            user.send_message(
                                user.translate('broadcast_start', user.broadcast(message_id)), keyboards.owner
                            )
                        case user.database.Menu.ADMIN_EDIT_AD_ID:
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
                        case user.database.Menu.ADMIN_EDIT_AD:
                            user.database.menu = user.database.Menu.ADMIN_MAIN
                            if user.edit_current_ad(message_id):
                                user.send_message(user.translate('ad_edited'), keyboards.owner)
                            else:
                                user.send_message(user.translate('ad_deleted'), keyboards.owner)
                        case user.database.Menu.ADMIN_BAN_VOTE:
                            if user.voice_exists(message) and \
                                    (target_voice := user.get_vote(message['voice']['file_unique_id'])):
                                functions.delete_vote_sync(target_voice.message_id, request.http_session)
                                target_voice.ban_sender()
                                user.database.menu = user.database.Menu.ADMIN_MAIN
                                user.send_message(user.translate('ban_voted'), keyboards.owner)
                        case user.database.Menu.ADMIN_DENY_VOICE:
                            if user.voice_exists(message) and \
                                    (target_voice := user.get_vote(message['voice']['file_unique_id'])):
                                user.deny_voice(target_voice)
                                user.database.menu = user.database.Menu.ADMIN_MAIN
                                user.send_message(user.translate('admin_voice_denied'), keyboards.owner)
                        case user.database.Menu.ADMIN_ACCEPT_VOICE:
                            if user.voice_exists(message) and \
                                    (target_voice := user.get_vote(message['voice']['file_unique_id'])):
                                user.accept_voice(target_voice)
                                user.database.menu = user.database.Menu.ADMIN_MAIN
                                user.send_message(user.translate('admin_voice_accepted'), keyboards.owner)
                        case user.database.Menu.ADMIN_GET_VOICE:
                            if search_result := functions.get_admin_voice(text):
                                user.send_voice(search_result.file_id, search_result.name)
                                user.database.menu = user.database.Menu.ADMIN_MAIN
                                user.send_message(
                                    user.translate('requested_voice'), keyboards.owner, message_id
                                )
                            else:
                                user.send_message(user.translate('voice_not_found'))
                        case user.database.Menu.ADMIN_SEND_EDIT_VOICE:
                            if user.voice_exists(message):
                                if target_voice := user.get_public_voice(message):
                                    user.database.current_voice = target_voice
                                    user.database.back_menu = 'send_edit_voice'
                                    user.database.menu = user.database.Menu.ADMIN_EDIT_VOICE
                                    user.send_message(translations.admin_messages['edit_voice'], keyboards.edit_voice)
                        case user.database.Menu.ADMIN_EDIT_VOICE:
                            match text:
                                case 'Edit Name':
                                    user.database.back_menu = 'edit_voice'
                                    user.database.menu = user.database.Menu.ADMIN_EDIT_VOICE_NAME
                                    user.send_message(translations.admin_messages['edit_voice_name'], keyboards.en_back)
                                case 'Edit Tags':
                                    user.database.back_menu = 'edit_voice'
                                    user.database.menu = user.database.Menu.ADMIN_EDIT_VOICE_TAGS
                                    user.send_message(translations.admin_messages['edit_voice_tags'], keyboards.en_back)
                                case 'Done ✔':
                                    user.database.menu = user.database.Menu.ADMIN_MAIN
                                    user.send_message(
                                        translations.admin_messages['voice_edited'], keyboards.owner, message_id
                                    )
                                case _:
                                    user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
                        case user.database.Menu.ADMIN_EDIT_VOICE_NAME:
                            if user.validate_voice_name(message):
                                user.edit_voice_name(text)
                                user.send_message(user.translate('voice_name_edited'), reply_to_message_id=message_id)
                                user.go_back()
                        case user.database.Menu.ADMIN_EDIT_VOICE_TAGS:
                            if user.process_voice_tags(text):
                                user.edit_voice_tags()
                                user.send_message(user.translate('voice_tags_edited'), reply_to_message_id=message_id)
                                user.go_back()
                        case user.database.Menu.ADMIN_FILE_ID:
                            if message.get('document'):
                                user.database.menu = user.database.Menu.ADMIN_MAIN
                                user.send_message(
                                    user.translate('file_id', message['document']['file_id']),
                                    keyboards.owner,
                                    message_id
                                )
                            else:
                                user.send_message(user.translate('no_document'), reply_to_message_id=message_id)
                        case user.database.Menu.ADMIN_VOICE_REVIEW:
                            if user.check_current_voice():
                                match text:
                                    case 'Edit Name':
                                        user.database.back_menu = 'voice_review'
                                        user.database.menu = user.database.Menu.ADMIN_EDIT_VOICE_NAME
                                        user.send_message(
                                            translations.admin_messages['edit_voice_name'], keyboards.en_back
                                        )
                                    case 'Edit Tags':
                                        user.database.back_menu = 'voice_review'
                                        user.database.menu = user.database.Menu.ADMIN_EDIT_VOICE_TAGS
                                        user.send_message(
                                            translations.admin_messages['edit_voice_tags'], keyboards.en_back
                                        )
                                    case 'Delete 🗑':
                                        user.delete_current_voice()
                                        if not user.assign_voice():
                                            user.go_back()
                                    case 'Check the Voice':
                                        user.database.current_voice.send_voice(
                                            user.database.chat_id, request.http_session
                                        )
                                    case 'Done ✔' | 'Done and Next ⏭':
                                        user.database.current_voice.reviewed = True
                                        user.database.current_voice.save()
                                        user.send_message(translations.admin_messages['reviewed'])
                                        if text == 'Done ✔':
                                            user.go_back()
                                        else:
                                            if not user.assign_voice():
                                                user.go_back()
                                    case _:
                                        user.send_message(
                                            user.translate('unknown_command'), reply_to_message_id=message_id
                                        )
                        case user.database.Menu.ADMIN_BROADCAST_STATUS:
                            try:
                                broadcast = models.Broadcast.objects.get(id=text)
                            except (models.Broadcast.DoesNotExist, ValueError):
                                user.send_message(
                                    user.translate('invalid_broadcast_id'), reply_to_message_id=message_id
                                )
                            else:
                                user.database.menu = user.database.Menu.ADMIN_MAIN
                                user.send_message(user.translate(
                                    'broadcast_status',
                                    broadcast.id,
                                    '✅' if broadcast.sent else '❌',
                                    models.User.objects.filter(last_broadcast=broadcast).count()
                                ), keyboards.owner, message_id)
                case models.User(status=user.database.Status.ACTIVE, rank=models.User.Rank.USER) |\
                        models.User(status=models.User.Status.ACTIVE, menu_mode=models.User.MenuMode.USER):
                    match user.database.menu:
                        case models.User.Menu.USER_MAIN:
                            user.database.back_menu = 'main'
                            match text:
                                case 'راهنما 🔰':
                                    user.database.menu = user.database.Menu.USER_HELP
                                    user.send_message(
                                        user.translate('help'),
                                        keyboards.help_keyboard(list(json.loads(settings.MEME_HELP_MESSAGES).keys()))
                                    )
                                case 'دیسکورد':
                                    user.send_message(
                                        user.translate('discord'), keyboards.discord, message_id
                                    )
                                case 'لغو رای گیری ⏹':
                                    if user.cancel_voting():
                                        user.send_message(
                                            user.translate('voting_canceled'), reply_to_message_id=message_id
                                        )
                                    else:
                                        user.send_message(user.translate('no_voting'), reply_to_message_id=message_id)
                                case 'حمایت مالی 💸':
                                    user.send_message(
                                        user.translate('donate'), reply_to_message_id=message_id, parse_mode='Markdown'
                                    )
                                case 'گروه عمومی':
                                    user.send_message(
                                        user.translate('group'), keyboards.group, message_id
                                    )
                                case 'آخرین ویس ها 🆕':
                                    user.send_ordered_voice_list(user.database.VoiceOrder.new_voice_id)
                                case 'ارتباط با مدیریت 📬':
                                    if user.sent_message:
                                        user.send_message(user.translate('pending_message'))
                                    else:
                                        user.database.menu = user.database.Menu.USER_CONTACT_ADMIN
                                        user.send_message(user.translate('send_message'), keyboards.per_back)
                                case 'ویس های پیشنهادی ✔':
                                    user.database.menu = user.database.Menu.USER_SUGGESTIONS
                                    user.send_message(user.translate('choices'), keyboards.manage_suggestions)
                                case 'ویس های محبوب 👌':
                                    user.send_ordered_voice_list(user.database.VoiceOrder.high_votes)
                                case 'پر استفاده ها ⭐':
                                    user.send_ordered_voice_list(user.database.VoiceOrder.high_usage)
                                case 'درخواست حذف ویس ✖':
                                    if user.database.deletes_user.exists():
                                        user.send_message(user.translate('pending_request'))
                                    else:
                                        user.database.menu = user.database.Menu.USER_DELETE_REQUEST
                                        user.send_message(user.translate('voice'), keyboards.per_back)
                                case 'ویس های شخصی 🔒':
                                    user.database.menu = user.database.Menu.USER_PRIVATE_VOICES
                                    user.send_message(user.translate('choices'), keyboards.manage_voice_list)
                                case 'علاقه مندی ها ❤️':
                                    user.database.menu = user.database.Menu.USER_FAVORITE_VOICES
                                    user.send_message(user.translate('choices'), keyboards.manage_voice_list)
                                case 'پلی لیست ▶️':
                                    user.database.menu = user.database.Menu.USER_PLAYLISTS
                                    user.send_message(user.translate('manage_playlists'), keyboards.manage_playlists)
                                case 'تنظیمات ⚙':
                                    user.database.menu = user.database.Menu.USER_SETTINGS
                                    user.send_message(user.translate('settings'), keyboards.settings)
                                case _ if 'voice' in message and (search_result := user.get_public_voice(message)):
                                    user.send_message(
                                        user.translate('voice_info', search_result.name),
                                        keyboards.use(search_result.id)
                                    )
                                case _:
                                    user.send_message(user.translate('unknown_command'))
                        case models.User.Menu.USER_CONTACT_ADMIN:
                            user.database.menu = user.database.Menu.USER_MAIN
                            user.contact_admin(message_id)
                            user.send_message(user.translate('message_sent'), keyboards.user, message_id)
                        case models.User.Menu.USER_SUGGEST_VOICE_NAME:
                            if text:
                                if user.validate_voice_name(message):
                                    user.database.menu = user.database.Menu.USER_SUGGEST_VOICE_TAGS
                                    user.database.temp_voice_name = text
                                    user.database.back_menu = 'suggest_name'
                                    user.send_message(user.translate('voice_tags'))
                            else:
                                user.send_message(user.translate('invalid_voice_name'))
                        case models.User.Menu.USER_SETTINGS:
                            match text:
                                case 'مرتب سازی 🗂':
                                    user.database.back_menu = 'settings'
                                    user.database.menu = user.database.Menu.USER_SORTING
                                    user.send_message(user.translate('select_order'), keyboards.voice_order)
                                case 'امتیازدهی ⭐':
                                    user.database.back_menu = 'settings'
                                    user.database.menu = user.database.Menu.USER_RANKING
                                    user.send_message(user.translate('choose'), keyboards.toggle)
                                case 'ویس های اخیر ⏱':
                                    user.database.back_menu = 'settings'
                                    user.database.menu = user.database.Menu.USER_RECENT_VOICES
                                    user.send_message(user.translate('choose'), keyboards.toggle)
                                case _:
                                    user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
                        case (models.User.Menu.USER_SUGGEST_VOICE_TAGS) if user.process_voice_tags(text):
                            user.database.menu = user.database.Menu.USER_SUGGEST_VOICE
                            user.database.back_menu = 'suggest_tags'
                            user.send_message(user.translate('send_voice'))
                        case (models.User.Menu.USER_SUGGEST_VOICE) if user.voice_exists(message):
                            if target_voice := user.add_voice(
                                    message['voice']['file_id'],
                                    message['voice']['file_unique_id'],
                                    models.Voice.Status.PENDING
                            ):
                                user.database.menu = user.database.Menu.USER_MAIN
                                target_voice.message_id = target_voice.send_voice(
                                    settings.MEME_CHANNEL,
                                    request.http_session,
                                    keyboards.suggestion_vote(target_voice.id)
                                )
                                tasks.check_voice(target_voice.id)
                                user.send_message(
                                    user.translate('suggestion_sent'),
                                    keyboards.user
                                )
                                target_voice.save()
                            else:
                                user.send_message(
                                    user.translate('voice_exists'), reply_to_message_id=message_id
                                )
                        case models.User.Menu.USER_RANKING:
                            match text:
                                case 'روشن 🔛' | 'خاموش 🔴':
                                    user.database.back_menu = 'main'
                                    user.database.menu = user.database.Menu.USER_SETTINGS
                                    if text == 'روشن 🔛':
                                        user.database.vote = True
                                        user.send_message(user.translate('voting_on'), keyboards.settings)
                                    else:
                                        user.database.vote = False
                                        user.send_message(user.translate('voting_off'), keyboards.settings)
                                case _:
                                    user.send_message(
                                        user.translate('unknown_command'), reply_to_message_id=message_id
                                    )
                        case models.User.Menu.USER_SORTING:
                            match text:
                                case (
                                    'جدید به قدیم' |
                                    'قدیم به جدید' |
                                    'بهترین به بدترین' |
                                    'بدترین به بهترین' |
                                    'پر استفاده به کم استفاده' |
                                    'کم استفاده به پر استفاده'
                                ):
                                    user.database.back_menu = 'main'
                                    user.database.menu = user.database.Menu.USER_SETTINGS
                                    user.send_message(user.translate('ordering_changed'), keyboards.settings)
                                    match text:
                                        case 'جدید به قدیم':
                                            user.database.voice_order = user.database.VoiceOrder.new_voice_id
                                        case 'قدیم به جدید':
                                            user.database.voice_order = user.database.VoiceOrder.voice_id
                                        case 'بهترین به بدترین':
                                            user.database.voice_order = user.database.VoiceOrder.high_votes
                                        case 'بدترین به بهترین':
                                            user.database.voice_order = user.database.VoiceOrder.votes
                                        case 'پر استفاده به کم استفاده':
                                            user.database.voice_order = user.database.VoiceOrder.high_usage
                                        case 'کم استفاده به پر استفاده':
                                            user.database.voice_order = user.database.VoiceOrder.low_usage
                                case _:
                                    user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
                        case models.User.Menu.USER_RECENT_VOICES:
                            match text:
                                case 'روشن 🔛' | 'خاموش 🔴':
                                    user.database.back_menu = 'main'
                                    user.database.menu = user.database.Menu.USER_SETTINGS
                                    if text == 'روشن 🔛':
                                        user.database.use_recent_voices = True
                                        user.send_message(user.translate('recent_voices_on'), keyboards.settings)
                                    else:
                                        user.database.use_recent_voices = False
                                        user.clear_recent_voices()
                                        user.send_message(user.translate('recent_voices_off'), keyboards.settings)
                                case _:
                                    user.send_message(user.translate('unknown_command'))
                        case (models.User.Menu.USER_DELETE_REQUEST) if user.voice_exists(message) and \
                                (target_voice := user.get_public_voice(message)):
                            owner = classes.User(
                                request.http_session,
                                classes.User.Mode.NORMAL,
                                instance=models.User.objects.get(rank='o')
                            )
                            user.database.menu = user.database.Menu.USER_MAIN
                            user.send_message(
                                user.translate('request_created'), keyboards.user, message_id
                            )
                            user.delete_request(target_voice)
                            owner.send_message('New delete request 🗑')
                        case models.User.Menu.USER_PRIVATE_VOICES:
                            match text:
                                case 'افزودن ویس ⏬':
                                    if user.private_voices_count <= 120:
                                        user.database.menu = user.database.Menu.USER_PRIVATE_VOICE_NAME
                                        user.database.back_menu = 'manage_private_voices'
                                        user.send_message(user.translate('voice_name'), keyboards.per_back)
                                    else:
                                        user.send_message(user.translate('voice_limit'))
                                case 'مشاهده ی ویس ها 📝':
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
                                case _:
                                    user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
                        case models.User.Menu.USER_PRIVATE_VOICE_NAME:
                            if text:
                                if user.validate_voice_name(message):
                                    user.database.temp_voice_name = text
                                    user.database.menu = user.database.Menu.USER_PRIVATE_VOICE_TAGS
                                    user.database.back_menu = 'private_name'
                                    user.send_message(user.translate('voice_tags'))
                            else:
                                user.send_message(user.translate('invalid_voice_name'))
                        case (models.User.Menu.USER_PRIVATE_VOICE_TAGS) if user.process_voice_tags(text):
                            user.database.menu = user.database.Menu.USER_PRIVATE_VOICE
                            user.database.back_menu = 'private_voice_tags'
                            user.send_message(user.translate('send_voice'))
                        case (models.User.Menu.USER_PRIVATE_VOICE) if user.voice_exists(message):
                            if user.create_private_voice(message):
                                user.database.menu = user.database.Menu.USER_PRIVATE_VOICES
                                user.database.back_menu = 'main'
                                user.send_message(user.translate('private_voice_added'), keyboards.manage_voice_list)
                            else:
                                user.send_message(user.translate('voice_exists'))
                        case (models.User.Menu.USER_MANAGE_PRIVATE_VOICE) if user.check_current_voice():
                            match text:
                                case 'حذف ویس ❌':
                                    if user.delete_private_voice():
                                        user.send_message(user.translate('voice_deleted'))
                                    else:
                                        user.send_message(user.translate('voice_deleted_before'))
                                    user.go_back()
                                case 'گوش دادن به ویس 🎧':
                                    user.send_voice(
                                        user.database.current_voice.file_id, user.database.current_voice.name
                                    )
                                case _:
                                    user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
                        case models.User.Menu.USER_FAVORITE_VOICES:
                            match text:
                                case 'افزودن ویس ⏬':
                                    if user.private_voices_count <= 120:
                                        user.database.menu = user.database.Menu.USER_FAVORITE_VOICE
                                        user.database.back_menu = 'manage_favorite_voices'
                                        user.send_message(user.translate('send_voice'), keyboards.per_back)
                                    else:
                                        user.send_message(user.translate('voice_limit'))
                                case 'مشاهده ی ویس ها 📝':
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
                                case _:
                                    user.send_message(user.translate('unknown_command'))
                        case (models.User.Menu.USER_FAVORITE_VOICE) if user.voice_exists(
                                message
                        ) and (current_voice := user.get_public_voice(message)):
                            if user.add_favorite_voice(current_voice):
                                user.database.menu = user.database.Menu.USER_FAVORITE_VOICES
                                user.database.back_menu = 'main'
                                user.send_message(
                                    user.translate('added_to_favorite'),
                                    keyboards.manage_voice_list
                                )
                            else:
                                user.send_message(user.translate('voice_exists_in_list'))
                        case (models.User.Menu.USER_MANAGE_FAVORITE_VOICE) if user.check_current_voice():
                            match text:
                                case 'حذف ویس ❌':
                                    if user.delete_favorite_voice():
                                        user.send_message(user.translate('deleted_from_list'))
                                    else:
                                        user.send_message(user.translate('voice_deleted_from_list_before'))
                                    user.go_back()
                                case 'گوش دادن به ویس 🎧':
                                    user.send_voice(
                                        user.database.current_voice.file_id, user.database.current_voice.name
                                    )
                                case _:
                                    user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
                        case models.User.Menu.USER_PLAYLISTS:
                            match text:
                                case 'ایجاد پلی لیست 🆕':
                                    user.database.back_menu = 'manage_playlists'
                                    user.database.menu = user.database.Menu.USER_CREATE_PLAYLIST
                                    user.send_message(user.translate('playlist_name'), keyboards.per_back)
                                case 'مشاهده پلی لیست ها 📝':
                                    current_page, prev_page, next_page = user.get_playlists(1)
                                    if current_page:
                                        user.send_message(
                                            functions.make_list_string(ObjectType.PLAYLIST, current_page),
                                            keyboards.make_list(
                                                keyboards.ObjectType.PLAYLIST, current_page, prev_page, next_page
                                            )
                                        )
                                    else:
                                        user.send_message(
                                            user.translate('no_playlist'), reply_to_message_id=message_id
                                        )
                                case _:
                                    user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
                        case models.User.Menu.USER_CREATE_PLAYLIST:
                            if text and len(text) <= 60:
                                user.send_message(
                                    user.translate('playlist_created', (user.create_playlist(text)).get_link())
                                )
                                user.go_back()
                            else:
                                user.send_message(
                                    user.translate('invalid_playlist_name'), reply_to_message_id=message_id
                                )
                        case models.User.Menu.USER_MANAGE_PLAYLIST:
                            match text:
                                case 'افزودن ویس ⏬':
                                    user.database.menu = user.database.Menu.USER_ADD_VOICE_PLAYLIST
                                    user.database.back_menu = 'manage_playlist'
                                    user.send_message(user.translate('send_private_voice'), keyboards.per_back)
                                case 'حذف پلی لیست ❌':
                                    user.delete_playlist()
                                    user.send_message(
                                        user.translate('playlist_deleted'), reply_to_message_id=message_id
                                    )
                                    user.go_back()
                                case 'مشاهده ی ویس ها 📝':
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
                                case 'لینک دعوت 🔗':
                                    user.send_message(user.translate(
                                        'playlist_link',
                                        user.database.current_playlist.name,
                                        user.database.current_playlist.get_link()
                                    ))
                                case 'مشترکین پلی لیست 👥':
                                    user.send_message(user.translate(
                                        'playlist_users_count', user.database.current_playlist.user_playlist.count()
                                    ))
                                case _:
                                    user.send_message(user.translate('unknown_command'))
                        case (models.User.Menu.USER_ADD_VOICE_PLAYLIST) if user.voice_exists(message):
                            if user.add_voice_to_playlist(message['voice']['file_unique_id']):
                                user.send_message(user.translate('added_to_playlist'))
                                user.go_back()
                            else:
                                user.send_message(
                                    user.translate('voice_is_not_yours'), reply_to_message_id=message_id
                                )
                        case (models.User.Menu.USER_MANAGE_PLAYLIST_VOICE) if user.check_current_voice():
                            match text:
                                case 'حذف ویس ❌':
                                    if user.remove_voice_from_playlist():
                                        user.send_message(user.translate('deleted_from_playlist'))
                                    else:
                                        user.send_message(user.translate('not_in_playlist'))
                                    user.go_back()
                                case 'گوش دادن به ویس 🎧':
                                    user.send_voice(
                                        user.database.current_voice.file_id, user.database.current_voice.name
                                    )
                                case _:
                                    user.send_message(user.translate('unknown_command'))
                        case models.User.Menu.USER_HELP:
                            help_messages = json.loads(settings.MEME_HELP_MESSAGES)
                            if text in help_messages:
                                user.send_animation(**help_messages[text], reply_to_message_id=message_id)
                            else:
                                user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
                        case models.User.Menu.USER_SUGGESTIONS:
                            match text:
                                case 'پیشنهاد ویس 🔥':
                                    user.add_sound()
                                case 'مشاهده ی ویس ها 📝':
                                    voices, prev_page, next_page = user.get_suggested_voices(1)
                                    if voices:
                                        user.send_message(
                                            functions.make_list_string(ObjectType.SUGGESTED_VOICE, voices),
                                            keyboards.make_list(
                                                ObjectType.SUGGESTED_VOICE, voices, prev_page, next_page
                                            )
                                        )
                                    else:
                                        user.send_message(
                                            user.translate('empty_suggested_voices'), reply_to_message_id=message_id
                                        )
                                case _:
                                    user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
                        case (models.User.Menu.USER_MANAGE_SUGGESTION) if user.check_current_voice():
                            match text:
                                case 'حذف ویس ❌':
                                    if user.delete_suggested_voice():
                                        user.send_message(user.translate('voice_deleted'))
                                    else:
                                        user.send_message(user.translate('voice_is_not_yours'))
                                    user.go_back()
                                case 'گوش دادن به ویس 🎧':
                                    user.send_voice(
                                        user.database.current_voice.file_id, user.database.current_voice.name
                                    )
                                case _:
                                    user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
            user.database.save()
    return HttpResponse(status=200)


def webhook_wrapper(request):
    request.http_session = RequestSession()
    return webhook(request)
