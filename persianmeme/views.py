from persianmeme import functions, classes, keyboards, models, tasks
from LilSholex.functions import (
    save_obj,
    delete_obj,
    get_obj,
    create_obj,
    filter_by_ordering,
    get_by_ordering,
    exists_obj,
    create_task,
    get_related_obj
)
from django.http import HttpResponse
import json
from aiohttp import ClientSession
from .types import ObjectType
from django.forms import ValidationError
from django.conf import settings


async def webhook(request):
    update = json.loads(request.body.decode())
    if 'inline_query' in update:
        query = update['inline_query']['query']
        offset = update['inline_query']['offset']
        inline_query_id = update['inline_query']['id']
        user = await classes.User(request.http_session, classes.User.Mode.SEND_AD, update['inline_query']['from']['id'])
        await user.upload_voice()
        if not user.database.started:
            await user.save()
            await functions.answer_inline_query(
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
        await user.send_ad()
        await user.set_username()
        await user.save()
        if user.database.status != 'f':
            results, next_offset = await user.get_voices(query, offset)
            await functions.answer_inline_query(
                inline_query_id, json.dumps(results), next_offset, 300, True, str(), str(), request.http_session
            )
    elif 'callback_query' in update:
        answer_query = functions.answer_callback_query(request.http_session)
        callback_query = update['callback_query']
        if callback_query['data'] == 'none':
            return HttpResponse(status=200)
        query_id = callback_query['id']
        inliner = await classes.User(
            request.http_session, classes.User.Mode.SEND_AD, callback_query['from']['id'], is_inline=True
        )
        await inliner.upload_voice()
        if not inliner.database.started:
            await answer_query(query_id, inliner.translate('start_to_use'), True)
            await inliner.save()
            return HttpResponse(status=200)
        await inliner.send_ad()
        callback_data = callback_query['data'].split(':')
        try:
            message = callback_query['message']
        except KeyError:
            message = None
            message_id = None
        else:
            message_id = message['message_id']
        if callback_data[0] == 'back':
            await inliner.go_back()
        elif callback_data[0].endswith('page'):
            object_type = ObjectType(int(callback_data[0].removesuffix('page')))
            page = int(callback_data[1])
            playlists, prev_page, next_page = await (
                inliner.get_playlists(page) if object_type is ObjectType.PLAYLIST
                else inliner.get_playlist_voices(page)
            )
            await inliner.edit_message_text(
                message_id,
                functions.make_list_string(object_type, playlists),
                keyboards.make_list(object_type, playlists, prev_page, next_page)
            )
        elif callback_type := ObjectType.check_value(callback_data[0]):
            if callback_type is ObjectType.PLAYLIST:
                try:
                    inliner.database.current_playlist = await get_related_obj(
                        models.Playlist.objects, id=callback_data[1], creator=inliner.database
                    )
                except (models.Playlist.DoesNotExist, ValueError):
                    await inliner.save()
                    return HttpResponse(status=200)
                inliner.database.menu = inliner.database.Menu.USER_MANAGE_PLAYLIST
                inliner.database.back_menu = 'manage_playlists'
                await answer_query(query_id, inliner.translate('managing_playlist'), False)
                await inliner.send_message(inliner.translate('manage_playlist'), keyboards.manage_playlist)
            else:
                try:
                    inliner.database.current_voice = await get_related_obj(
                        await inliner.playlist_voices, voice_id=callback_data[1]
                    )
                except models.Voice.DoesNotExist:
                    await inliner.save()
                    return HttpResponse(status=200)
                inliner.database.menu = inliner.database.Menu.USER_MANAGE_PLAYLIST_VOICE
                inliner.database.back_menu = 'manage_playlist'
                await answer_query(query_id, inliner.translate('managing_voice'), False)
                await inliner.send_message(inliner.translate('manage_voice'), keyboards.manage_voice)
        elif callback_data[0] in (message_options := ('read', 'ban', 'reply')):
            await inliner.delete_message(message_id)
            if not (target_message := await functions.get_message(callback_data[1])):
                await inliner.save()
                return HttpResponse(status=200)
            user = await classes.User(
                request.http_session, classes.User.Mode.NORMAL, instance=target_message.sender, is_inline=True
            )
            await user.send_message(user.translate('checked_by_admin'))
            if callback_data[0] == message_options[0]:
                await answer_query(query_id, inliner.translate('read'), False)
            elif callback_data[0] == message_options[1]:
                await user.send_message(user.translate('you_are_banned'))
                user.database.status = user.database.Status.BANNED
                await answer_query(query_id, inliner.translate('banned', user.database.chat_id), True)
                await user.save()
            elif callback_data[0] == message_options[2]:
                inliner.database.menu = inliner.database.Menu.ADMIN_MESSAGE_USER
                inliner.database.menu_mode = inliner.database.MenuMode.ADMIN
                inliner.database.back_menu = 'chat_id'
                inliner.database.temp_user_id = user.database.chat_id
                await inliner.send_message(inliner.translate('reply'), keyboards.en_back)
                await answer_query(query_id, inliner.translate('replying'), False)
        elif callback_data[0] in ('admin_accept', 'admin_deny'):
            if callback_data[0] == 'admin_deny':
                if await inliner.delete_semi_active(message['voice']['file_unique_id']):
                    await answer_query(query_id, inliner.translate('deleted'), False)
                else:
                    await answer_query(query_id, inliner.translate('processed_before'), False)
            elif callback_data[0] == 'admin_accept':
                if await functions.accept_voice(message['voice']['file_unique_id']):
                    await answer_query(query_id, inliner.translate('accepted'), False)
                else:
                    await answer_query(query_id, inliner.translate('processed_before'), False)
            await inliner.delete_message(message_id)
        elif callback_data[0] in ('delete', 'delete_deny'):
            target_delete = await functions.get_delete(callback_data[1])
            if not target_delete:
                return HttpResponse(status=200)
            user = await classes.User(
                request.http_session, classes.User.Mode.NORMAL, instance=await target_delete.get_user(), is_inline=True
            )
            if callback_data[0] == 'delete':
                await functions.delete_target_voice(target_delete)
                answer_query(query_id, user.translate('deleted'), True)
                await user.send_message(user.translate('deleted'))
            elif callback_data[0] == 'delete_deny':
                await delete_obj(target_delete)
                answer_query(query_id, inliner.translate('denied'), True)
                await user.send_message(user.translate('delete_denied'))
            await inliner.delete_message(message_id)
        elif callback_data[0] in ('accept', 'deny') and message.get('voice'):
            target_voice = await functions.check_voice(message['voice']['file_unique_id'])
            if target_voice:
                if callback_data[0] == 'accept':
                    if not await inliner.like_voice(target_voice):
                        await answer_query(query_id, inliner.translate('vote_before'), True)
                    else:
                        await answer_query(query_id, inliner.translate('voted'), False)
                else:
                    if not await inliner.dislike_voice(target_voice):
                        await answer_query(query_id, inliner.translate('vote_before'), True)
                    else:
                        await answer_query(query_id, inliner.translate('voted'), False)
                await save_obj(target_voice)
        elif callback_data[0] in ('up', 'down'):
            try:
                voice = await get_obj(models.Voice, voice_id=callback_data[1])
            except models.Voice.DoesNotExist:
                await inliner.save()
                return HttpResponse(status=200)
            if callback_data[0] == 'up':
                if inliner.database in await voice.get_voters():
                    await answer_query(query_id, inliner.translate('voted_before'), True)
                else:
                    await inliner.add_voter(voice)
                    voice.votes += 1
                    await save_obj(voice)
                    await answer_query(query_id, inliner.translate('voice_voted'), False)
            elif callback_data[0] == 'down':
                if inliner.database in await voice.get_voters():
                    await inliner.remove_voter(voice)
                    voice.votes -= 1
                    await save_obj(voice)
                    await answer_query(query_id, inliner.translate('took_vote_back'), False)
                else:
                    await answer_query(query_id, inliner.translate('not_voted'), True)
        await inliner.save()
    else:
        if 'message' in update:
            message = update['message']
        else:
            return HttpResponse(status=200)
        text = message.get('text', None)
        message_id = message['message_id']
        if message['chat']['id'] < 0:
            return HttpResponse(status=200)
        user = await classes.User(request.http_session, classes.User.Mode.SEND_AD, message['chat']['id'])
        await user.set_username()
        await user.send_ad()
        user.database.started = True
        if text in ('بازگشت 🔙', 'Back 🔙'):
            await user.go_back()
            return HttpResponse(status=200)
        if user.database.rank != user.database.Rank.USER:
            if text == '/admin':
                await user.menu_cleanup()
                user.database.menu_mode = user.database.MenuMode.ADMIN
                user.database.menu = user.database.Menu.ADMIN_MAIN
                await user.send_message(user.translate('admin_panel'), keyboards.owner, message_id)
                await user.save()
                return HttpResponse(status=200)
            elif text == '/user':
                await user.menu_cleanup()
                user.database.menu_mode = user.database.MenuMode.USER
                user.database.menu = user.database.Menu.USER_MAIN
                await user.send_message(user.translate('user_panel'), keyboards.user, message_id)
                await user.save()
                return HttpResponse(status=200)
        if user.database.rank != user.database.Rank.USER and user.database.menu_mode == user.database.MenuMode.ADMIN:
            if text == '/start':
                await user.menu_cleanup()
                user.database.menu = user.database.Menu.ADMIN_MAIN
                await user.send_message(user.translate('welcome'), keyboards.owner, message_id)
            elif user.database.menu == user.database.Menu.ADMIN_MAIN:
                user.database.back_menu = 'main'
                # All Admins Section
                if text == 'Add Sound':
                    user.database.menu = user.database.Menu.ADMIN_VOICE_NAME
                    await user.send_message(user.translate('voice_name'), keyboards.en_back)
                elif text == 'Voice Count':
                    await user.send_message(await functions.count_voices())
                elif text == 'Member Count':
                    await user.send_message(user.translate('member_count', await functions.count_users()))
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
                        await user.send_message(user.translate('chat_id'), keyboards.en_back)
                    elif text == admin_options[1]:
                        user.database.menu = user.database.Menu.ADMIN_BAN_USER
                        await user.send_message(user.translate('chat_id'), keyboards.en_back)
                    elif text == admin_options[2]:
                        user.database.menu = user.database.Menu.ADMIN_UNBAN_USER
                        await user.send_message(user.translate('chat_id'), keyboards.en_back)
                    elif text == admin_options[3]:
                        user.database.menu = user.database.Menu.ADMIN_FULL_BAN_USER
                        await user.send_message(user.translate('chat_id'), keyboards.en_back)
                    elif text == admin_options[4]:
                        user.database.menu = user.database.Menu.ADMIN_DELETE_VOICE
                        await user.send_message(user.translate('voice'), keyboards.en_back)
                    elif text == admin_options[5]:
                        if accepted_voices := await functions.get_all_accepted():
                            for voice in accepted_voices:
                                await user.send_voice(voice.file_id, voice.name, {'inline_keyboard': [[
                                    {'text': 'Accept', 'callback_data': 'admin_accept'},
                                    {'text': 'Deny', 'callback_data': 'admin_deny'}
                                ]]})
                            await user.send_message(
                                user.translate('accepted_voices'), reply_to_message_id=message_id
                            )
                        else:
                            await user.send_message(
                                user.translate('no_accepted'), reply_to_message_id=message_id
                            )
                    elif text == admin_options[6]:
                        user.database.menu = user.database.Menu.ADMIN_BAN_VOTE
                        await user.send_message(user.translate('voice'), keyboards.en_back)
                    elif text == admin_options[7]:
                        user.database.menu = user.database.Menu.ADMIN_ACCEPT_VOICE
                        await user.send_message(user.translate('voice'), keyboards.en_back)
                    elif text == admin_options[8]:
                        user.database.menu = user.database.Menu.ADMIN_DENY_VOICE
                        await user.send_message(user.translate('voice'), keyboards.en_back)
                    elif text == admin_options[9]:
                        user.database.menu = user.database.Menu.ADMIN_GET_VOICE
                        await user.send_message(
                            user.translate('send_voice_id'), keyboards.en_back
                        )
                    elif text == admin_options[10]:
                        user.database.menu = user.database.Menu.ADMIN_SEND_EDIT_VOICE
                        await user.send_message(
                            user.translate('send_edit_voice'), keyboards.en_back
                        )
                    else:
                        user.database.menu = user.database.Menu.ADMIN_FILE_ID
                        await user.send_message(user.translate('send_file_id'), keyboards.en_back)
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
                        await user.send_message(user.translate('chat_id'), keyboards.en_back)
                    elif text == owner_options[1]:
                        user.database.menu = user.database.Menu.ADMIN_ADD_AD
                        await user.send_message(user.translate('send_ad'), keyboards.en_back)
                    elif text == owner_options[2]:
                        user.database.menu = user.database.Menu.ADMIN_DELETE_AD
                        await user.send_message(user.translate('send_ad_id'), keyboards.en_back)
                    elif text == owner_options[3]:
                        delete_requests = await functions.get_delete_requests()
                        if delete_requests:
                            for delete_request in delete_requests:
                                await user.send_voice(
                                    (await delete_request.get_voice()).file_id,
                                    f'From : {(await delete_request.get_user()).chat_id}',
                                    keyboards.delete_voice(delete_request.delete_id)
                                )
                            await user.send_message(
                                user.translate('delete_requests'), reply_to_message_id=message_id
                            )
                        else:
                            await user.send_message(
                                user.translate('no_delete_requests'), reply_to_message_id=message_id
                            )
                    elif text == owner_options[4]:
                        user.database.menu = user.database.Menu.ADMIN_BROADCAST
                        await user.send_message(user.translate('broadcast'), keyboards.en_back)
                    elif text == owner_options[5]:
                        user.database.menu = user.database.Menu.ADMIN_EDIT_AD_ID
                        await user.send_message(user.translate('edit_ad'), keyboards.en_back)
                    else:
                        await user.send_messages()
                elif 'voice' in message:
                    if search_result := await user.get_public_voice(message):
                        target_voice_name = search_result.name
                        await user.send_message(
                            user.translate('voice_info', target_voice_name),
                            keyboards.use(target_voice_name)
                        )
                else:
                    await user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.ADMIN_VOICE_NAME:
                if text:
                    if await user.validate_voice_name(message):
                        user.database.menu = user.database.Menu.ADMIN_VOICE_TAGS
                        user.database.temp_voice_name = text
                        user.database.back_menu = 'voice_name'
                        await user.send_message(user.translate('voice_tags'))
                else:
                    await user.send_message(user.translate('voice_name'))
            elif user.database.menu == user.database.Menu.ADMIN_VOICE_TAGS:
                if await user.process_voice_tags(text):
                    user.database.menu = user.database.Menu.ADMIN_NEW_VOICE
                    user.database.back_menu = 'voice_tags'
                    await user.send_message(user.translate('voice'))
            elif user.database.menu == user.database.Menu.ADMIN_NEW_VOICE:
                if await user.voice_exists(message):
                    if await user.add_voice(
                            message['voice']['file_id'],
                            message['voice']['file_unique_id'],
                            models.Voice.Status.ACTIVE
                    ):
                        user.database.menu = user.database.Menu.ADMIN_MAIN
                        await user.send_message(user.translate('voice_added'), keyboards.owner)
                    else:
                        await user.send_message(user.translate('voice_is_added'))
            elif user.database.menu == user.database.Menu.ADMIN_DELETE_VOICE:
                if await user.voice_exists(message):
                    await user.delete_voice(message['voice']['file_unique_id'])
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    await user.send_message(user.translate('deleted'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_BAN_USER:
                try:
                    user_id = int(text)
                except (ValueError, TypeError):
                    await user.send_message(user.translate('invalid_user_id'))
                else:
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    await functions.change_user_status(user_id, models.User.Status.BANNED)
                    await user.send_message(
                        user.translate('banned', user_id),
                        keyboards.owner
                    )
            elif user.database.menu == user.database.Menu.ADMIN_UNBAN_USER:
                try:
                    user_id = int(text)
                except (ValueError, TypeError):
                    await user.send_message(user.translate('invalid_user_id'))
                else:
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    await functions.change_user_status(user_id, models.User.Status.ACTIVE)
                    await user.send_message(user.translate('unbanned'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_FULL_BAN_USER:
                try:
                    user_id = int(text)
                except (ValueError, TypeError):
                    await user.send_message(user.translate('invalid_user_id'))
                else:
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    await functions.change_user_status(user_id, models.User.Status.FULL_BANNED)
                    await user.send_message(user.translate('banned', user_id), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_MESSAGE_USER_ID:
                try:
                    user.database.temp_user_id = int(text)
                except (ValueError, TypeError):
                    await user.send_message(user.translate('invalid_user_id'))
                else:
                    user.database.menu = user.database.Menu.ADMIN_MESSAGE_USER
                    user.database.back_menu = 'chat_id'
                    await user.send_message(user.translate('message'))
            elif user.database.menu == user.database.Menu.ADMIN_MESSAGE_USER:
                user.database.menu = user.database.Menu.ADMIN_MAIN
                await user.copy_message(message_id, keyboards.admin_message, chat_id=user.database.temp_user_id)
                await user.send_message(user.translate('sent'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_ADD_AD:
                user.database.menu = user.database.Menu.ADMIN_MAIN
                ad_id = (await create_obj(models.Ad, chat_id=user.database.chat_id, message_id=message_id)).ad_id
                await user.send_message(
                    user.translate('ad_submitted', ad_id), keyboards.owner
                )
            elif user.database.menu == user.database.Menu.ADMIN_DELETE_AD:
                try:
                    await delete_obj(await get_obj(models.Ad, ad_id=int(text)))
                except (ValueError, models.Ad.DoesNotExist):
                    await user.send_message(
                        user.translate('invalid_ad_id'), reply_to_message_id=message_id
                    )
                else:
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    await user.send_message(user.translate('ad_deleted'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_GET_USER:
                if text:
                    try:
                        int(text)
                    except ValueError:
                        await user.send_message(
                            user.translate('invalid_user_id'), reply_to_message_id=message_id
                        )
                    else:
                        user.database.menu = user.database.Menu.ADMIN_MAIN
                        await user.send_message(
                            user.translate('user_profile', text),
                            keyboards.owner,
                            message_id,
                            'Markdown'
                        )
                else:
                    await user.send_message(user.translate('invalid_user_id'))
            elif user.database.menu == user.database.Menu.ADMIN_BROADCAST:
                await user.broadcast(message_id)
                user.database.menu = user.database.Menu.ADMIN_MAIN
                await user.send_message(user.translate('broadcast_start'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_EDIT_AD_ID:
                try:
                    await user.set_current_ad(text)
                except (models.Ad.DoesNotExist, ValueError):
                    await user.send_message(
                        user.translate('invalid_ad_id'), reply_to_message_id=message_id
                    )
                else:
                    user.database.back_menu = 'edit_ad'
                    user.database.menu = user.database.Menu.ADMIN_EDIT_AD
                    await user.send_message(user.translate('replace_ad'), keyboards.en_back)
            elif user.database.menu == user.database.Menu.ADMIN_EDIT_AD:
                user.database.menu = user.database.Menu.ADMIN_MAIN
                if await user.edit_current_ad(message_id):
                    await user.send_message(user.translate('ad_edited'), keyboards.owner)
                else:
                    await user.send_message(user.translate('ad_deleted'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_BAN_VOTE:
                if await user.voice_exists(message) and \
                        (target_voice := await user.get_vote(message['voice']['file_unique_id'])):
                    await functions.delete_vote_async(target_voice.message_id, request.http_session)
                    await target_voice.ban_sender()
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    await user.send_message(user.translate('ban_voted'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_DENY_VOICE:
                if await user.voice_exists(message) and \
                        (target_voice := await user.get_vote(message['voice']['file_unique_id'])):
                    await user.deny_voice(target_voice)
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    await user.send_message(user.translate('admin_voice_denied'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_ACCEPT_VOICE:
                if await user.voice_exists(message) and \
                        (target_voice := await user.get_vote(message['voice']['file_unique_id'])):
                    await user.accept_voice(target_voice)
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    await user.send_message(user.translate('admin_voice_accepted'), keyboards.owner)
            elif user.database.menu == user.database.Menu.ADMIN_GET_VOICE:
                if search_result := await functions.get_admin_voice(text):
                    await user.send_voice(search_result.file_id, search_result.name)
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    await user.send_message(
                        user.translate('requested_voice'), keyboards.owner, message_id
                    )
                else:
                    await user.send_message(user.translate('voice_not_found'))
            elif user.database.menu == user.database.Menu.ADMIN_SEND_EDIT_VOICE:
                if await user.voice_exists(message):
                    if target_voice := await user.get_public_voice(message):
                        user.database.current_voice = target_voice
                        user.database.back_menu = 'send_edit_voice'
                        user.database.menu = user.database.Menu.ADMIN_EDIT_VOICE
                        await user.send_message(user.translate('edit_voice'), keyboards.edit_voice)
            elif user.database.menu == user.database.Menu.ADMIN_EDIT_VOICE:
                if text in (edit_options := ('Edit Name', 'Edit Tags')):
                    user.database.back_menu = 'edit_voice'
                    if text == edit_options[0]:
                        user.database.menu = user.database.Menu.ADMIN_EDIT_VOICE_NAME
                        await user.send_message(user.translate('edit_voice_name'), keyboards.en_back)
                    else:
                        user.database.menu = user.database.Menu.ADMIN_EDIT_VOICE_TAGS
                        await user.send_message(user.translate('edit_voice_tags'), keyboards.en_back)
                else:
                    await user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
            elif user.database.menu == user.database.Menu.ADMIN_EDIT_VOICE_NAME:
                if await user.validate_voice_name(message):
                    await user.edit_voice_name(text)
                    await user.send_message(user.translate('voice_name_edited'), reply_to_message_id=message_id)
                    await user.go_back()
            elif user.database.menu == user.database.Menu.ADMIN_EDIT_VOICE_TAGS:
                if await user.process_voice_tags(text):
                    await user.edit_voice_tags()
                    await user.send_message(user.translate('voice_tags_edited'), reply_to_message_id=message_id)
                    await user.go_back()
            elif user.database.menu == user.database.Menu.ADMIN_FILE_ID:
                if message.get('document'):
                    user.database.menu = user.database.Menu.ADMIN_MAIN
                    await user.send_message(
                        user.translate('file_id', message['document']['file_id']),
                        keyboards.owner,
                        message_id
                    )
                else:
                    await user.send_message(user.translate('no_document'), reply_to_message_id=message_id)
        elif user.database.status == user.database.Status.ACTIVE and \
                (user.database.rank == user.database.Rank.USER or
                 user.database.menu_mode == user.database.MenuMode.USER):
            if text and text.startswith('/start'):
                if len(splinted_text := text.split(' ')) == 2 and splinted_text[1] != 'new_user':
                    try:
                        if result := await user.join_playlist(splinted_text[1]):
                            await user.send_message(
                                user.translate('joined_playlist', result.name), keyboards.user
                            )
                        else:
                            await user.send_message(
                                user.translate('already_joined_playlist'), keyboards.user
                            )
                    except (models.Playlist.DoesNotExist, ValidationError):
                        await user.send_message(user.translate('invalid_playlist'), keyboards.user)
                else:
                    await user.send_message(user.translate('welcome'), keyboards.user)
                user.database.menu_mode = user.database.MenuMode.USER
                user.database.menu = user.database.Menu.USER_MAIN
            elif user.database.menu == user.database.Menu.USER_MAIN:
                user.database.back_menu = 'main'
                if text == 'راهنما 🔰':
                    user.database.menu = user.database.Menu.USER_HELP
                    await user.send_message(
                        user.translate('help'),
                        keyboards.help_keyboard(list(json.loads(settings.MEME_HELP_MESSAGES).keys()))
                    )
                elif text == 'دیسکورد':
                    await user.send_message(
                        user.translate('discord'), keyboards.discord, message_id
                    )
                elif text == 'لغو رای گیری ⏹':
                    await user.send_message(
                        user.translate('voting_voice'),
                        keyboards.per_back,
                        message_id
                    )
                    user.database.menu = user.database.Menu.USER_CANCEL_VOTING
                    user.database.menu = user.database.Menu.USER_CANCEL_VOTING
                elif text == 'حمایت مالی 💸':
                    await user.send_message(
                        user.translate('donate'), reply_to_message_id=message_id, parse_mode='Markdown'
                    )
                elif text == 'گروه عمومی':
                    await user.send_message(
                        user.translate('group'), keyboards.group, message_id
                    )
                elif text == 'آخرین ویس ها 🆕':
                    voices_str = ''
                    for voice in await filter_by_ordering(
                            models.Voice, '-voice_id', 15, status__in=models.PUBLIC_STATUS, voice_type='n'
                    ):
                        voices_str += f'⭕ {voice.name}\n'
                    await user.send_message(voices_str)
                elif text == 'ارتباط با مدیریت 📬':
                    if await user.sent_message:
                        await user.send_message(user.translate('pending_message'))
                    else:
                        user.database.menu = user.database.Menu.USER_CONTACT_ADMIN
                        await user.send_message(user.translate('send_message'), keyboards.per_back)
                elif text == 'پیشنهاد ویس 🔥':
                    if await user.has_pending_voice():
                        await user.send_message(user.translate('pending_voice'))
                    else:
                        user.database.menu = user.database.Menu.USER_SUGGEST_VOICE_NAME
                        await user.send_message(user.translate('voice_name'), keyboards.per_back)
                elif text == 'حذف ویس ❌':
                    user.database.menu = user.database.Menu.USER_DELETE_SUGGESTION
                    await user.send_message(
                        user.translate('delete_suggestion'), keyboards.per_back
                    )
                elif text == 'ویس های محبوب 👌':
                    voices_str = ''
                    for voice in await get_by_ordering(models.Voice, '-votes', 15):
                        voices_str += f'⭕ {voice.name}\n'
                    await user.send_message(voices_str)
                elif text == 'امتیازدهی ⭐':
                    user.database.menu = user.database.Menu.USER_RANKING
                    await user.send_message(user.translate('choose'), keyboards.toggle)
                elif text == 'مرتب سازی 🗂':
                    user.database.menu = user.database.Menu.USER_SORTING
                    await user.send_message(user.translate('select_order'), keyboards.voice_order)
                elif text == 'درخواست حذف ویس ✖':
                    if await exists_obj(user.database.deletes_user):
                        await user.send_message(user.translate('pending_request'))
                    else:
                        user.database.menu = user.database.Menu.USER_DELETE_REQUEST
                        await user.send_message(user.translate('voice'), keyboards.per_back)
                elif text == 'ویس های شخصی 🔒':
                    user.database.menu = user.database.Menu.USER_PRIVATE_VOICES
                    await user.send_message(user.translate('choices'), keyboards.private)
                elif text == 'علاقه مندی ها ❤️':
                    user.database.menu = user.database.Menu.USER_FAVORITE_VOICES
                    await user.send_message(user.translate('choices'), keyboards.private)
                elif text == 'پلی لیست ▶️':
                    user.database.menu = user.database.Menu.USER_PLAYLISTS
                    await user.send_message(user.translate('manage_playlists'), keyboards.manage_playlists)
                elif 'voice' in message:
                    if search_result := await user.get_public_voice(message):
                        await user.send_message(
                            user.translate('voice_info', search_result.name),
                            keyboards.use(search_result.name)
                        )
                else:
                    await user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_CONTACT_ADMIN:
                user.database.menu = user.database.Menu.USER_MAIN
                await user.contact_admin(message_id)
                await user.send_message(user.translate('message_sent'), keyboards.user, message_id)
            elif user.database.menu == user.database.Menu.USER_SUGGEST_VOICE_NAME:
                if text:
                    if await user.validate_voice_name(message):
                        user.database.menu = user.database.Menu.USER_SUGGEST_VOICE_TAGS
                        user.database.temp_voice_name = text
                        user.database.back_menu = 'suggest_name'
                        await user.send_message(user.translate('voice_tags'))
                else:
                    await user.send_message(user.translate('invalid_voice_name'))
            elif user.database.menu == user.database.Menu.USER_SUGGEST_VOICE_TAGS:
                if await user.process_voice_tags(text):
                    user.database.menu = user.database.Menu.USER_SUGGEST_VOICE
                    user.database.back_menu = 'suggest_tags'
                    await user.send_message(user.translate('send_voice'))
            elif user.database.menu == user.database.Menu.USER_SUGGEST_VOICE:
                if await user.voice_exists(message):
                    if target_voice := await user.add_voice(
                        message['voice']['file_id'],
                        message['voice']['file_unique_id'],
                        models.Voice.Status.PENDING
                    ):
                        user.database.menu = user.database.Menu.USER_MAIN
                        target_voice.message_id = await target_voice.send_voice(request.http_session)
                        await create_task(tasks.check_voice, target_voice.voice_id)
                        await create_task(tasks.update_votes, target_voice.voice_id)
                        await user.send_message(
                            user.translate('suggestion_sent'),
                            keyboards.user
                        )
                        await save_obj(target_voice)
                    else:
                        await user.send_message(
                            user.translate('voice_exists'), reply_to_message_id=message_id
                        )
            elif user.database.menu == user.database.Menu.USER_DELETE_SUGGESTION:
                if await user.voice_exists(message):
                    if await user.remove_voice(message['voice']['file_unique_id']):
                        user.database.menu = user.database.Menu.USER_MAIN
                        await user.send_message(user.translate('voice_deleted'), keyboards.user)
                    else:
                        await user.send_message(user.translate('voice_is_not_yours'))
            elif user.database.menu == user.database.Menu.USER_RANKING:
                if text == 'روشن 🔛':
                    user.database.vote = True
                    user.database.menu = user.database.Menu.USER_MAIN
                    await user.send_message(user.translate('voting_on'), keyboards.user)
                elif text == 'خاموش 🔴':
                    user.database.vote = False
                    user.database.menu = user.database.Menu.USER_MAIN
                    await user.send_message(user.translate('voting_off'), keyboards.user)
                else:
                    await user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_SORTING:
                if text == 'جدید به قدیم':
                    user.database.voice_order = '-voice_id'
                    user.database.menu = user.database.Menu.USER_MAIN
                    await user.send_message(user.translate('ordering_changed'), keyboards.user)
                elif text == 'قدیم به جدید':
                    user.database.voice_order = 'voice_id'
                    user.database.menu = user.database.Menu.USER_MAIN
                    await user.send_message(user.translate('ordering_changed'), keyboards.user)
                elif text == 'بهترین به بدترین':
                    user.database.voice_order = '-votes'
                    user.database.menu = user.database.Menu.USER_MAIN
                    await user.send_message(user.translate('ordering_changed'), keyboards.user)
                elif text == 'بدترین به بهترین':
                    user.database.voice_order = 'votes'
                    user.database.menu = user.database.Menu.USER_MAIN
                    await user.send_message(user.translate('ordering_changed'), keyboards.user)
                else:
                    await user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_DELETE_REQUEST:
                if await user.voice_exists(message):
                    if target_voice := await user.get_public_voice(message):
                        owner = await classes.User(
                            request.http_session, classes.User.Mode.NORMAL, instance=await functions.get_owner()
                        )
                        user.database.menu = user.database.Menu.USER_MAIN
                        await user.send_message(
                            user.translate('request_created'), keyboards.user, message_id
                        )
                        await user.delete_request(target_voice)
                        await owner.send_message('New delete request 🗑')
            elif user.database.menu == user.database.Menu.USER_PRIVATE_VOICES:
                if text == 'افزودن ⏬':
                    if await user.private_voices_count() <= 120:
                        user.database.menu = user.database.Menu.USER_PRIVATE_VOICE_NAME
                        user.database.back_menu = 'private'
                        await user.send_message(user.translate('voice_name'), keyboards.per_back)
                    else:
                        await user.send_message(user.translate('voice_limit'))
                elif text == 'حذف 🗑':
                    user.database.menu = user.database.Menu.USER_DELETE_PRIVATE_VOICE
                    user.database.back_menu = 'private'
                    await user.send_message(user.translate('send_voice'), keyboards.per_back)
                else:
                    await user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_PRIVATE_VOICE_NAME:
                if text:
                    if await user.validate_voice_name(message):
                        user.database.temp_voice_name = text
                        user.database.menu = user.database.Menu.USER_PRIVATE_VOICE_TAGS
                        user.database.back_menu = 'private_name'
                        await user.send_message(user.translate('voice_tags'))
                else:
                    await user.send_message(user.translate('invalid_voice_name'))
            elif user.database.menu == user.database.Menu.USER_PRIVATE_VOICE_TAGS:
                if await user.process_voice_tags(text):
                    user.database.menu = user.database.Menu.USER_PRIVATE_VOICE
                    user.database.back_menu = 'private_voice_tags'
                    await user.send_message(user.translate('send_voice'))
            elif user.database.menu == user.database.Menu.USER_PRIVATE_VOICE:
                if await user.voice_exists(message):
                    if await user.create_private_voice(message):
                        user.database.menu = user.database.Menu.USER_PRIVATE_VOICES
                        user.database.back_menu = 'main'
                        await user.send_message(user.translate('private_voice_added'), keyboards.private)
                    else:
                        await user.send_message(user.translate('voice_exists'))
            elif user.database.menu == user.database.Menu.USER_DELETE_PRIVATE_VOICE:
                if await user.voice_exists(message):
                    if await user.delete_private_voice(message['voice']['file_unique_id']):
                        user.database.menu = user.database.Menu.USER_PRIVATE_VOICES
                        user.database.back_menu = 'main'
                        await user.send_message(user.translate('voice_deleted'), keyboards.private)
                    else:
                        await user.send_message(user.translate('voice_is_not_yours'))
            elif user.database.menu == user.database.Menu.USER_FAVORITE_VOICES:
                if text == 'افزودن ⏬':
                    if await user.count_favorite_voices() <= 30:
                        user.database.menu = user.database.Menu.USER_FAVORITE_VOICE
                        user.database.back_menu = 'favorite'
                        await user.send_message(user.translate('send_voice'), keyboards.per_back)
                    else:
                        await user.send_message(user.translate('voice_limit'))
                elif text == 'حذف 🗑':
                    user.database.menu = user.database.Menu.USER_DELETE_FAVORITE_VOICE
                    user.database.back_menu = 'favorite'
                    await user.send_message(user.translate('send_voice'), keyboards.per_back)
                else:
                    await user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_FAVORITE_VOICE:
                if await user.voice_exists(message):
                    if current_voice := await user.get_public_voice(message):
                        if await user.add_favorite_voice(current_voice):
                            user.database.menu = user.database.Menu.USER_FAVORITE_VOICES
                            user.database.back_menu = 'main'
                            await user.send_message(
                                user.translate('added_to_favorite'),
                                keyboards.private
                            )
                        else:
                            await user.send_message(user.translate('voice_exists_in_list'))
            elif user.database.menu == user.database.Menu.USER_DELETE_FAVORITE_VOICE:
                if await user.voice_exists(message):
                    if current_voice := await user.get_public_voice(message):
                        await user.delete_favorite_voice(current_voice)
                        user.database.menu = user.database.Menu.USER_FAVORITE_VOICES
                        user.database.back_menu = 'main'
                        await user.send_message(user.translate('deleted_from_list'), keyboards.private)
            elif user.database.menu == user.database.Menu.USER_CANCEL_VOTING:
                if await user.voice_exists(message):
                    if await user.cancel_voting(message['voice']['file_unique_id']):
                        user.database.menu = user.database.Menu.USER_MAIN
                        await user.send_message(
                            user.translate('voting_canceled'), keyboards.user, message_id
                        )
                    else:
                        await user.send_message(
                            user.translate('voice_not_found'), reply_to_message_id=message_id
                        )
            elif user.database.menu == user.database.Menu.USER_PLAYLISTS:
                if text == 'ایجاد پلی لیست 🆕':
                    user.database.back_menu = 'manage_playlists'
                    user.database.menu = user.database.Menu.USER_CREATE_PLAYLIST
                    await user.send_message(user.translate('playlist_name'), keyboards.per_back)
                elif text == 'مشاهده پلی لیست ها 📝':
                    current_page, prev_page, next_page = await user.get_playlists(1)
                    if current_page:
                        await user.send_message(
                            functions.make_list_string(ObjectType.PLAYLIST, current_page),
                            keyboards.make_list(keyboards.ObjectType.PLAYLIST, current_page, prev_page, next_page)
                        )
                    else:
                        await user.send_message(
                            user.translate('no_playlist'), reply_to_message_id=message_id
                        )
                else:
                    await user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_CREATE_PLAYLIST:
                if text and len(text) <= 60:
                    await user.send_message(
                        user.translate('playlist_created', (await user.create_playlist(text)).get_link())
                    )
                    await user.go_back()
                else:
                    await user.send_message(
                        user.translate('invalid_playlist_name'), reply_to_message_id=message_id
                    )
            elif user.database.menu == user.database.Menu.USER_MANAGE_PLAYLIST:
                if text == 'افزودن ویس ⏬':
                    user.database.menu = user.database.Menu.USER_ADD_VOICE_PLAYLIST
                    user.database.back_menu = 'manage_playlist'
                    await user.send_message(user.translate('send_private_voice'), keyboards.per_back)
                elif text == 'حذف پلی لیست ❌':
                    await user.delete_playlist()
                    await user.send_message(
                        user.translate('playlist_deleted'), reply_to_message_id=message_id
                    )
                    await user.go_back()
                elif text == 'مشاهده ی ویس ها 📝':
                    voices, prev_page, next_page = await user.get_playlist_voices(1)
                    if voices:
                        await user.send_message(
                            functions.make_list_string(ObjectType.VOICE, voices),
                            keyboards.make_list(ObjectType.VOICE, voices, prev_page, next_page)
                        )
                    else:
                        await user.send_message(
                            user.translate('empty_playlist'), reply_to_message_id=message_id
                        )
                elif text == 'لینک دعوت 🔗':
                    await user.send_message(
                        user.translate('playlist_link', await user.playlist_name, await user.playlist_link)
                    )
                elif text == 'مشترکین پلی لیست 👥':
                    await user.send_message(user.translate('playlist_users_count', await user.playlist_users))
                else:
                    await user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_ADD_VOICE_PLAYLIST:
                if await user.voice_exists(message):
                    if await user.add_voice_to_playlist(message['voice']['file_unique_id']):
                        await user.send_message(user.translate('added_to_playlist'))
                        await user.go_back()
                    else:
                        await user.send_message(
                            user.translate('voice_is_not_yours'), reply_to_message_id=message_id
                        )
            elif user.database.menu == user.database.Menu.USER_MANAGE_PLAYLIST_VOICE:
                if text == 'حذف ویس ❌':
                    if await user.remove_voice_from_playlist():
                        await user.send_message(user.translate('deleted_from_playlist'))
                    else:
                        await user.send_message(user.translate('not_in_playlist'))
                    await user.go_back()
                elif text == 'گوش دادن به ویس 🎧':
                    file_id, name = await user.voice_info
                    await user.send_voice(file_id, name)
                else:
                    await user.send_message(user.translate('unknown_command'))
            elif user.database.menu == user.database.Menu.USER_HELP:
                help_messages = json.loads(settings.MEME_HELP_MESSAGES)
                if text in help_messages:
                    await user.send_animation(**help_messages[text], reply_to_message_id=message_id)
                else:
                    await user.send_message(user.translate('unknown_command'))
        await user.save()
    return HttpResponse(status=200)


async def webhook_wrapper(request):
    async with ClientSession() as http_session:
        request.http_session = http_session
        return await webhook(request)
