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
from . import translations
from .types import ObjectType
from django.forms import ValidationError


async def webhook(request):
    update = json.loads(request.body.decode())
    answer_query = functions.answer_callback_query(request.http_session)
    if 'inline_query' in update:
        query = update['inline_query']['query']
        offset = update['inline_query']['offset']
        inline_query_id = update['inline_query']['id']
        user = await classes.User(request.http_session, classes.User.Mode.SEND_AD, update['inline_query']['from']['id'])
        await user.record_audio()
        if not user.database.started:
            await user.save()
            await functions.answer_inline_query(
                inline_query_id, functions.start_bot_first(), '', 0, request.http_session
            )
            return HttpResponse(status=200)
        await user.send_ad()
        await user.set_username()
        await user.save()
        if user.database.status != 'f':
            results, next_offset = await user.get_voices(query, offset)
            await functions.answer_inline_query(
                inline_query_id, json.dumps(results), next_offset, 300, request.http_session
            )
    elif 'callback_query' in update:
        callback_query = update['callback_query']
        if callback_query['data'] == 'none':
            return HttpResponse(status=200)
        query_id = callback_query['id']
        inliner = await classes.User(request.http_session, classes.User.Mode.SEND_AD, callback_query['from']['id'])
        await inliner.record_audio()
        if not inliner.database.started:
            await answer_query(query_id, translations.user_messages['start_to_use'], True)
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
                inliner.database.menu = 21
                inliner.database.back_menu = 'manage_playlists'
                await inliner.send_message(translations.user_messages['manage_playlist'], keyboards.manage_playlist)
            else:
                try:
                    inliner.database.current_voice = await get_related_obj(
                        await inliner.playlist_voices, voice_id=callback_data[1]
                    )
                except models.Voice.DoesNotExist:
                    await inliner.save()
                    return HttpResponse(status=200)
                inliner.database.menu = 23
                inliner.database.back_menu = 'manage_playlist'
                await inliner.send_message(translations.user_messages['manage_voice'], keyboards.manage_voice)
        elif callback_data[0] == 'read':
            user = await classes.User(request.http_session, classes.User.Mode.NORMAL, callback_data[1])
            user.database.sent_message = False
            await user.send_message(translations.user_messages['checked_by_admin'])
            await inliner.delete_message(message_id)
            await answer_query(query_id, 'Read ✅', False)
            await user.save()
        elif callback_data[0] == 'ban':
            user = await classes.User(request.http_session, classes.User.Mode.NORMAL, callback_data[1])
            user.database.sent_message = False
            user.database.status = 'b'
            await user.send_message(translations.user_messages['you_are_banned'])
            await inliner.delete_message(message_id)
            await answer_query(query_id, translations.admin_messages['banned'].format(user.database.chat_id), True)
            await user.save()
        elif callback_data[0] == 'reply':
            user = await classes.User(request.http_session, classes.User.Mode.NORMAL, callback_data[1])
            inliner.database.menu = 9
            inliner.database.back_menu = 'chat_id'
            inliner.database.temp_user_id = user.database.chat_id
            await inliner.send_message(translations.admin_messages['reply'], keyboards.en_back)
            await inliner.delete_message(message_id)
            await answer_query(query_id, translations.admin_messages['replying'], False)
            user.database.sent_message = False
            await user.send_message(translations.user_messages['checked_by_admin'])
            await user.save()
        elif callback_data[0] in ('admin_accept', 'admin_deny'):
            if callback_data[0] == 'admin_deny':
                if await inliner.delete_semi_active(message['voice']['file_unique_id']):
                    await answer_query(query_id, translations.admin_messages['deleted'], False)
                else:
                    await answer_query(query_id, translations.admin_messages['processed_before'], False)
            elif callback_data[0] == 'admin_accept':
                if await functions.accept_voice(message['voice']['file_unique_id']):
                    await answer_query(query_id, translations.admin_messages['accepted'], False)
                else:
                    await answer_query(query_id, 'Voice has been processed before ✖️', False)
            await inliner.delete_message(message_id)
        elif callback_data[0] in ('delete', 'delete_deny'):
            target_delete = await functions.get_delete(callback_data[1])
            if not target_delete:
                return HttpResponse(status=200)
            user = await classes.User(
                request.http_session, classes.User.Mode.NORMAL, instance=await target_delete.get_user()
            )
            if callback_data[0] == 'delete':
                await functions.delete_target_voice(target_delete)
                answer_query(query_id, translations.admin_messages['deleted'], True)
                await user.send_message(translations.user_messages['deleted'])
            elif callback_data[0] == 'delete_deny':
                await delete_obj(target_delete)
                answer_query(query_id, translations.admin_messages['denied'], True)
                await user.send_message(translations.user_messages['delete_denied'])
            await inliner.delete_message(message_id)
        elif callback_data[0] in ('accept', 'deny') and message.get('voice'):
            target_voice = await functions.check_voice(message['voice']['file_unique_id'])
            if target_voice:
                if callback_data[0] == 'accept':
                    if not await inliner.like_voice(target_voice):
                        await answer_query(query_id, translations.user_messages['vote_before'], True)
                    else:
                        await answer_query(query_id, translations.user_messages['voted'], False)
                else:
                    if not await inliner.dislike_voice(target_voice):
                        await answer_query(query_id, translations.user_messages['vote_before'], True)
                    else:
                        await answer_query(query_id, translations.user_messages['voted'], False)
                await save_obj(target_voice)
        elif callback_data[0] in ('up', 'down'):
            try:
                voice = await get_obj(models.Voice, voice_id=callback_data[1])
            except models.Voice.DoesNotExist:
                await inliner.save()
                return HttpResponse(status=200)
            if callback_data[0] == 'up':
                if inliner.database in await voice.get_voters():
                    await answer_query(query_id, translations.user_messages['voted_before'], True)
                else:
                    await inliner.add_voter(voice)
                    voice.votes += 1
                    await save_obj(voice)
                    await answer_query(query_id, translations.user_messages['voice_voted'], False)
            elif callback_data[0] == 'down':
                if inliner.database in await voice.get_voters():
                    await inliner.remove_voter(voice)
                    voice.votes -= 1
                    await save_obj(voice)
                    await answer_query(query_id, translations.user_messages['took_vote_back'], False)
                else:
                    await answer_query(query_id, translations.user_messages['not_voted'], True)
        await inliner.save()
    else:
        if 'message' in update:
            message = update['message']
        elif 'edited_message' in update:
            message = update['edited_message']
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
                user.database.menu_mode = user.database.MenuMode.ADMIN
                user.database.menu = 1
                await user.send_message(translations.admin_messages['admin_panel'], keyboards.owner, message_id)
                await user.save()
                return HttpResponse(status=200)
            elif text == '/user':
                user.database.menu_mode = user.database.MenuMode.USER
                user.database.menu = 1
                await user.send_message(translations.user_messages['user_panel'], keyboards.user, message_id)
                await user.save()
                return HttpResponse(status=200)
        if user.database.rank != 'u' and user.database.menu_mode == user.database.MenuMode.ADMIN:
            if text == '/start':
                user.database.menu = 1
                await user.send_message(translations.admin_messages['welcome'], keyboards.owner, message_id)
            elif user.database.menu == 1:
                user.database.back_menu = 'main'
                # All Admins Section
                if text == 'Add Sound':
                    user.database.menu = 2
                    await user.send_message(translations.admin_messages['voice_name'], keyboards.en_back)
                elif text == 'Voice Count':
                    await user.send_message(await functions.count_voices())
                elif text == 'Member Count':
                    await user.send_message(
                        translations.admin_messages['member_count'].format(await functions.count_users())
                    )
                # Admins & Owner section
                elif user.database.rank in models.BOT_ADMINS and text in (
                    'Get User',
                    'Ban a User',
                    'Unban a User',
                    'Full Ban',
                    'Delete Sound',
                    'Accepted',
                    'Ban Vote'
                ):
                    if text == 'Get User':
                        user.database.menu = 12
                        await user.send_message(translations.admin_messages['chat_id'], keyboards.en_back)
                    elif text == 'Ban a User':
                        user.database.menu = 5
                        await user.send_message(translations.admin_messages['chat_id'], keyboards.en_back)
                    elif text == 'Unban a User':
                        user.database.menu = 6
                        await user.send_message(translations.admin_messages['chat_id'], keyboards.en_back)
                    elif text == 'Full Ban':
                        user.database.menu = 7
                        await user.send_message(translations.admin_messages['chat_id'], keyboards.en_back)
                    elif text == 'Delete Sound':
                        user.database.menu = 4
                        await user.send_message(translations.admin_messages['voice'], keyboards.en_back)
                    elif text == 'Accepted':
                        if accepted_voices := await functions.get_all_accepted():
                            for voice in accepted_voices:
                                await user.send_voice(voice.file_id, voice.name, {'inline_keyboard': [[
                                    {'text': 'Accept', 'callback_data': 'admin_accept'},
                                    {'text': 'Deny', 'callback_data': 'admin_deny'}
                                ]]})
                            await user.send_message(
                                translations.admin_messages['accepted_voices'], reply_to_message_id=message_id
                            )
                        else:
                            await user.send_message(
                                translations.admin_messages['no_accepted'], reply_to_message_id=message_id
                            )
                    elif text == 'Ban Vote':
                        user.database.menu = 16
                        await user.send_message(translations.admin_messages['send_a_voice'], keyboards.en_back)
                # Owner Section
                elif user.database.rank == user.database.Rank.OWNER and text in (
                        'Message User', 'Add Ad', 'Delete Ad', 'Delete Requests', 'Broadcast', 'Edit Ad'
                ):
                    if text == 'Message User':
                        user.database.menu = 8
                        await user.send_message(translations.admin_messages['chat_id'], keyboards.en_back)
                    elif text == 'Add Ad':
                        user.database.menu = 10
                        await user.send_message(translations.admin_messages['send_ad'], keyboards.en_back)
                    elif text == 'Delete Ad':
                        user.database.menu = 11
                        await user.send_message(translations.admin_messages['send_ad_id'], keyboards.en_back)
                    elif text == 'Delete Requests':
                        delete_requests = await functions.get_delete_requests()
                        if delete_requests:
                            for delete_request in delete_requests:
                                await user.send_voice(
                                    (await delete_request.get_voice()).file_id,
                                    f'From : {(await delete_request.get_user()).chat_id}',
                                    keyboards.delete_voice(delete_request.delete_id)
                                )
                            await user.send_message(
                                translations.admin_messages['delete_requests'], reply_to_message_id=message_id
                            )
                        else:
                            await user.send_message(
                                translations.admin_messages['no_delete_requests'], reply_to_message_id=message_id
                            )
                    elif text == 'Broadcast':
                        user.database.menu = 13
                        await user.send_message(translations.admin_messages['broadcast'], keyboards.en_back)
                    elif text == 'Edit Ad':
                        user.database.menu = 14
                        await user.send_message(translations.admin_messages['edit_ad'], keyboards.en_back)
                elif 'voice' in message:
                    search_result = await functions.get_voice(message['voice']['file_unique_id'])
                    if search_result:
                        target_voice_name = search_result.name
                        await user.send_message(
                            translations.admin_messages['voice_info'].format(target_voice_name),
                            keyboards.use(target_voice_name)
                        )
                    else:
                        await user.send_message(translations.admin_messages['voice_not_found'])
                else:
                    await user.send_message(translations.admin_messages['unknown'])
            elif user.database.menu == 2:
                if text:
                    if len(text) > 50:
                        await user.send_message(translations.admin_messages['name_limit'])
                    else:
                        user.database.menu = 3
                        user.database.temp_voice_name = text
                        user.database.back_menu = 'voice_name'
                        await user.send_message(translations.admin_messages['voice'])
                else:
                    await user.send_message(translations.admin_messages['voice_name'])
            elif user.database.menu == 3:
                if await user.voice_exists(message):
                    if await functions.add_voice(
                            message['voice']['file_id'],
                            message['voice']['file_unique_id'],
                            user.database.temp_voice_name,
                            user.database,
                            'a'
                    ):
                        user.database.menu = 1
                        await user.send_message(translations.admin_messages['voice_added'], keyboards.owner)
                    else:
                        await user.send_message(translations.admin_messages['voice_is_added'])
            elif user.database.menu == 4:
                if await user.voice_exists(message):
                    await user.delete_voice(message['voice']['file_unique_id'])
                    user.database.menu = 1
                    await user.send_message(translations.admin_messages['deleted'], keyboards.owner)
            elif user.database.menu == 5:
                try:
                    user_id = int(text)
                except (ValueError, TypeError):
                    await user.send_message(translations.admin_messages['invalid_user_id'])
                else:
                    user.database.menu = 1
                    await functions.change_user_status(user_id, 'b')
                    await user.send_message(
                        translations.admin_messages['banned'].format(user_id),
                        keyboards.owner
                    )
            elif user.database.menu == 6:
                try:
                    user_id = int(text)
                except (ValueError, TypeError):
                    await user.send_message(translations.admin_messages['invalid_user_id'])
                else:
                    user.database.menu = 1
                    await functions.change_user_status(user_id, 'a')
                    await user.send_message(translations.admin_messages['unbanned'], keyboards.owner)
            elif user.database.menu == 7:
                try:
                    user_id = int(text)
                except (ValueError, TypeError):
                    await user.send_message(translations.admin_messages['invalid_user_id'])
                else:
                    user.database.menu = 1
                    await functions.change_user_status(user_id, 'f')
                    await user.send_message(translations.admin_messages['banned'].format(user_id), keyboards.owner)
            elif user.database.menu == 8:
                try:
                    user.database.temp_user_id = int(text)
                except (ValueError, TypeError):
                    await user.send_message(translations.admin_messages['invalid_user_id'])
                else:
                    user.database.menu = 9
                    user.database.back_menu = 'chat_id'
                    await user.send_message(translations.admin_messages['message'])
            elif user.database.menu == 9:
                user.database.menu = 1
                await user.copy_message(user.database.temp_user_id, message_id, keyboards.admin_message)
                await user.send_message(translations.admin_messages['sent'], keyboards.owner)
            elif user.database.menu == 10:
                user.database.menu = 1
                ad_id = (await create_obj(models.Ad, chat_id=user.database.chat_id, message_id=message_id)).ad_id
                await user.send_message(
                    translations.admin_messages['ad_submitted'].format(ad_id), keyboards.owner
                )
            elif user.database.menu == 11:
                try:
                    await delete_obj(await get_obj(models.Ad, ad_id=int(text)))
                except (ValueError, models.Ad.DoesNotExist):
                    await user.send_message(
                        translations.admin_messages['invalid_ad_id'], reply_to_message_id=message_id
                    )
                else:
                    user.database.menu = 1
                    await user.send_message(translations.admin_messages['ad_deleted'], keyboards.owner)
            elif user.database.menu == 12:
                if text:
                    try:
                        int(text)
                    except ValueError:
                        await user.send_message(
                            translations.admin_messages['invalid_user_id'], reply_to_message_id=message_id
                        )
                    else:
                        user.database.menu = 1
                        await user.send_message(
                            translations.admin_messages['user_profile'].format(text),
                            keyboards.owner,
                            message_id,
                            'Markdown'
                        )
                else:
                    await user.send_message(translations.admin_messages['invalid_user_id'])
            elif user.database.menu == 13:
                await user.broadcast(message_id)
                user.database.menu = 1
                await user.send_message(translations.admin_messages['broadcast_start'], keyboards.owner)
            elif user.database.menu == 14:
                try:
                    await user.set_current_ad(text)
                except (models.Ad.DoesNotExist, TypeError):
                    await user.send_message(
                        translations.admin_messages['invalid_ad_id'], reply_to_message_id=message_id
                    )
                else:
                    user.database.back_menu = 'edit_ad'
                    user.database.menu = 15
                    await user.send_message(translations.admin_messages['replace_ad'], keyboards.en_back)
            elif user.database.menu == 15:
                user.database.menu = 1
                if await user.edit_current_ad(message_id):
                    await user.send_message(translations.admin_messages['ad_edited'], keyboards.owner)
                else:
                    await user.send_message(translations.admin_messages['ad_deleted'], keyboards.owner)
            elif user.database.menu == 16:
                if user.voice_exists(message):
                    if target_voice := await functions.get_vote(message['voice']['file_unique_id']):
                        await functions.delete_vote_async(target_voice.message_id, request.http_session)
                        await target_voice.ban_sender()
                        user.database.menu = 1
                        await user.send_message(translations.admin_messages['ban_voted'], keyboards.owner)
                    else:
                        await user.send_message(translations.admin_messages['voice_not_found'])
        elif user.database.status == user.database.Status.ACTIVE and \
                (user.database.rank == user.database.Rank.USER or
                 user.database.menu_mode == user.database.MenuMode.USER):
            if text and text.startswith('/start'):
                if len(splinted_text := text.split(' ')) == 2:
                    try:
                        if result := await user.join_playlist(splinted_text[1]):
                            await user.send_message(
                                translations.user_messages['joined_playlist'].format(result.name), keyboards.user
                            )
                        else:
                            await user.send_message(
                                translations.user_messages['already_joined_playlist'], keyboards.user
                            )
                    except (models.Playlist.DoesNotExist, ValidationError):
                        await user.send_message(translations.user_messages['invalid_playlist'], keyboards.user)
                else:
                    await user.send_message(translations.user_messages['welcome'], keyboards.user)
                user.database.menu = 1
            elif user.database.menu == 1:
                user.database.back_menu = 'main'
                if text == 'راهنما 🔰':
                    await user.send_help()
                elif text == 'دیسکورد':
                    await user.send_message(
                        translations.user_messages['discord'], keyboards.discord, message_id
                    )
                elif text == 'لغو رای گیری ⏹':
                    await user.send_message(
                        translations.user_messages['voting_voice'],
                        keyboards.per_back,
                        message_id
                    )
                    user.database.menu = 18
                elif text == 'حمایت مالی 💸':
                    await user.send_message(
                        translations.user_messages['donate'], reply_to_message_id=message_id, parse_mode='Markdown'
                    )
                elif text == 'گروه عمومی':
                    await user.send_message(
                        translations.user_messages['group'], keyboards.group, message_id
                    )
                elif text == 'آخرین ویس ها 🆕':
                    voices_str = ''
                    for voice in (await filter_by_ordering(
                            models.Voice, '-voice_id', status__in=models.PUBLIC_STATUS, voice_type='n'
                    ))[:15]:
                        voices_str += f'⭕ {voice.name}\n'
                    await user.send_message(voices_str)
                elif text == 'ارتباط با مدیریت 📬':
                    if user.database.sent_message:
                        await user.send_message(translations.user_messages['pending_message'])
                    else:
                        user.database.menu = 2
                        await user.send_message(translations.user_messages['send_message'], keyboards.per_back)
                elif text == 'پیشنهاد ویس 🔥':
                    if await user.has_pending_voice():
                        await user.send_message(translations.user_messages['pending_voice'])
                    else:
                        user.database.menu = 3
                        await user.send_message(translations.user_messages['voice_name'], keyboards.per_back)
                elif text == 'حذف ویس ❌':
                    user.database.menu = 5
                    await user.send_message(
                        translations.user_messages['delete_suggestion'], keyboards.per_back
                    )
                elif text == 'ویس های محبوب 👌':
                    voices_str = ''
                    for voice in (await get_by_ordering(models.Voice, '-votes'))[:15]:
                        voices_str += f'⭕ {voice.name}\n'
                    await user.send_message(voices_str)
                elif text == 'امتیازدهی ⭐':
                    user.database.menu = 6
                    await user.send_message(translations.user_messages['choose'], keyboards.toggle)
                elif text == 'مرتب سازی 🗂':
                    user.database.menu = 7
                    await user.send_message(translations.user_messages['select_order'], keyboards.voice_order)
                elif text == 'درخواست حذف ویس ✖':
                    if await exists_obj(user.database.deletes_user):
                        await user.send_message(translations.user_messages['pending_request'])
                    else:
                        user.database.menu = 8
                        await user.send_message(translations.user_messages['voice'], keyboards.per_back)
                elif text == 'ویس های شخصی 🔒':
                    user.database.menu = 11
                    await user.send_message(translations.user_messages['choices'], keyboards.private)
                elif text == 'علاقه مندی ها ❤️':
                    user.database.menu = 15
                    await user.send_message(translations.user_messages['choices'], keyboards.private)
                elif text == 'پلی لیست ▶️':
                    user.database.menu = 19
                    await user.send_message(translations.user_messages['manage_playlists'], keyboards.manage_playlists)
                elif 'voice' in message:
                    search_result = await functions.get_voice(message['voice']['file_unique_id'])
                    if search_result:
                        await user.send_message(
                            translations.user_messages['voice_info'].format(search_result.name),
                            keyboards.use(search_result.name)
                        )
                    else:
                        await user.send_message(translations.user_messages['voice_not_found'])
                else:
                    await user.send_message(translations.user_messages['unknown_command'])
            elif user.database.menu == 2:
                user.database.menu = 1
                owner = await functions.get_owner()
                await user.copy_message(owner.chat_id, message_id, keyboards.message(user.database.chat_id))
                user.database.sent_message = True
                await user.send_message(translations.user_messages['message_sent'], keyboards.user, message_id)
            elif user.database.menu == 3:
                if text:
                    if message.get('entities') or len(text) > 50:
                        await user.send_message(translations.user_messages['invalid_voice_name'])
                    else:
                        user.database.menu = 4
                        user.database.temp_voice_name = text
                        user.database.back_menu = 'suggest_name'
                        await user.send_message(translations.user_messages['send_voice'])
                else:
                    await user.send_message(translations.user_messages['invalid_voice_name'])
            elif user.database.menu == 4:
                if await user.voice_exists(message):
                    target_voice = await functions.add_voice(
                        message['voice']['file_id'],
                        message['voice']['file_unique_id'],
                        user.database.temp_voice_name,
                        user.database,
                        'p'
                    )
                    if target_voice:
                        user.database.menu = 1
                        target_voice.message_id = await target_voice.send_voice(request.http_session)
                        await create_task(tasks.check_voice, target_voice.voice_id)
                        await create_task(tasks.update_votes, target_voice.voice_id)
                        await user.send_message(
                            translations.user_messages['suggestion_sent'],
                            keyboards.user
                        )
                        await save_obj(target_voice)
                    else:
                        await user.send_message(
                            translations.user_messages['voice_exists'], reply_to_message_id=message_id
                        )
            elif user.database.menu == 5:
                if await user.voice_exists(message):
                    if await user.remove_voice(message['voice']['file_unique_id']):
                        user.database.menu = 1
                        await user.send_message(translations.user_messages['voice_deleted'], keyboards.user)
                    else:
                        await user.send_message(translations.user_messages['voice_is_not_yours'])
            elif user.database.menu == 6:
                if text == 'روشن 🔛':
                    user.database.vote = True
                    user.database.menu = 1
                    await user.send_message(translations.user_messages['voting_on'], keyboards.user)
                elif text == 'خاموش 🔴':
                    user.database.vote = False
                    user.database.menu = 1
                    await user.send_message(translations.user_messages['voting_off'], keyboards.user)
                else:
                    await user.send_message(translations.user_messages['unknown_command'])
            elif user.database.menu == 7:
                if text == 'جدید به قدیم':
                    user.database.voice_order = '-voice_id'
                    user.database.menu = 1
                    await user.send_message(translations.user_messages['ordering_changed'], keyboards.user)
                elif text == 'قدیم به جدید':
                    user.database.voice_order = 'voice_id'
                    user.database.menu = 1
                    await user.send_message(translations.user_messages['ordering_changed'], keyboards.user)
                elif text == 'بهترین به بدترین':
                    user.database.voice_order = '-votes'
                    user.database.menu = 1
                    await user.send_message(translations.user_messages['ordering_changed'], keyboards.user)
                elif text == 'بدترین به بهترین':
                    user.database.voice_order = 'votes'
                    user.database.menu = 1
                    await user.send_message(translations.user_messages['ordering_changed'], keyboards.user)
                else:
                    await user.send_message(translations.user_messages['unknown_command'])
            elif user.database.menu == 8:
                if await user.voice_exists(message):
                    target_voice = await functions.get_voice(
                        message['voice']['file_unique_id']
                    )
                    if target_voice:
                        owner = await classes.User(
                            request.http_session, classes.User.Mode.NORMAL, instance=await functions.get_owner()
                        )
                        user.database.menu = 1
                        await user.send_message(
                            translations.user_messages['request_created'], keyboards.user, message_id
                        )
                        await user.delete_request(target_voice)
                        await owner.send_message('New delete request 🗑')
                    else:
                        await user.send_message(translations.user_messages['voice_not_found'])
            elif user.database.menu == 11:
                if text == 'افزودن ⏬':
                    if await user.private_user_count() <= 60:
                        user.database.menu = 12
                        user.database.back_menu = 'private'
                        await user.send_message(translations.user_messages['voice_name'], keyboards.per_back)
                    else:
                        await user.send_message(translations.user_messages['voice_limit'])
                elif text == 'حذف 🗑':
                    user.database.menu = 13
                    user.database.back_menu = 'private'
                    await user.send_message(translations.user_messages['send_voice'], keyboards.per_back)
                else:
                    await user.send_message(translations.user_messages['unknown_command'])
            elif user.database.menu == 12:
                if text:
                    if len(text) > 50:
                        await user.send_message(translations.user_messages['invalid_voice_name'])
                    else:
                        user.database.temp_voice_name = text
                        user.database.menu = 14
                        user.database.back_menu = 'private_name'
                        await user.send_message(translations.user_messages['send_voice'])
                else:
                    await user.send_message(translations.user_messages['invalid_voice_name'])
            elif user.database.menu == 13:
                if await user.voice_exists(message):
                    current_voice = await functions.get_voice(
                        message['voice']['file_unique_id'], voice_type='p'
                    )
                    if current_voice:
                        if await user.delete_private_voice(current_voice):
                            user.database.menu = 11
                            user.database.back_menu = 'main'
                            await user.send_message(translations.user_messages['voice_deleted'], keyboards.private)
                        else:
                            await user.send_message(translations.user_messages['voice_is_not_yours'])
                    else:
                        await user.send_message(translations.user_messages['voice_not_found'])
            elif user.database.menu == 14:
                if await user.voice_exists(message):
                    if not await functions.get_voice(message['voice']['file_unique_id']):
                        await user.create_private_voice(message)
                        user.database.menu = 11
                        user.database.back_menu = 'main'
                        await user.send_message('این ویس به لیست ویس های شما اضافه شد ✅', keyboards.private)
                    else:
                        await user.send_message('این ویس در ربات موجود است ❌')
            elif user.database.menu == 15:
                if text == 'افزودن ⏬':
                    if await user.count_favorite_voices() <= 30:
                        user.database.menu = 16
                        user.database.back_menu = 'favorite'
                        await user.send_message(translations.user_messages['send_voice'], keyboards.per_back)
                    else:
                        await user.send_message(translations.user_messages['voice_limit'])
                elif text == 'حذف 🗑':
                    user.database.menu = 17
                    user.database.back_menu = 'favorite'
                    await user.send_message(translations.user_messages['send_voice'], keyboards.per_back)
                else:
                    await user.send_message(translations.user_messages['unknown_command'])
            elif user.database.menu == 16:
                if await user.voice_exists(message):
                    current_voice = await functions.get_voice(message['voice']['file_unique_id'])
                    if current_voice:
                        if await user.add_favorite_voice(current_voice):
                            user.database.menu = 15
                            user.database.back_menu = 'main'
                            await user.send_message(
                                translations.user_messages['added_to_favorite'],
                                keyboards.private
                            )
                        else:
                            await user.send_message(translations.user_messages['voice_exists_in_list'])
                    else:
                        await user.send_message(translations.user_messages['voice_not_found'])
            elif user.database.menu == 17:
                if await user.voice_exists(message):
                    current_voice = await functions.get_voice(message['voice']['file_unique_id'])
                    if current_voice:
                        await user.delete_favorite_voice(current_voice)
                        user.database.menu = 15
                        user.database.back_menu = 'main'
                        await user.send_message(translations.user_messages['deleted_from_list'], keyboards.private)
                    else:
                        await user.send_message(translations.user_messages['voice_not_found'])
            elif user.database.menu == 18:
                if await user.voice_exists(message):
                    if await user.cancel_voting(message['voice']['file_unique_id']):
                        user.database.menu = 1
                        await user.send_message(
                            translations.user_messages['voting_canceled'], keyboards.user, message_id
                        )
                    else:
                        await user.send_message(
                            translations.user_messages['voice_not_found'], reply_to_message_id=message_id
                        )
            elif user.database.menu == 19:
                if text == 'ایجاد پلی لیست 🆕':
                    user.database.back_menu = 'manage_playlists'
                    user.database.menu = 20
                    await user.send_message(translations.user_messages['playlist_name'], keyboards.per_back)
                elif text == 'مشاهده پلی لیست ها 📝':
                    current_page, prev_page, next_page = await user.get_playlists(1)
                    if current_page:
                        await user.send_message(
                            functions.make_list_string(ObjectType.PLAYLIST, current_page),
                            keyboards.make_list(keyboards.ObjectType.PLAYLIST, current_page, prev_page, next_page)
                        )
                    else:
                        await user.send_message(
                            translations.user_messages['no_playlist'], reply_to_message_id=message_id
                        )
                else:
                    await user.send_message(translations.user_messages['unknown_command'])
            elif user.database.menu == 20:
                if text and len(text) <= 60:
                    await user.send_message(
                        translations.user_messages['playlist_created'].format(
                            (await user.create_playlist(text)).get_link()
                        )
                    )
                    await user.go_back()
                else:
                    await user.send_message(
                        translations.user_messages['invalid_playlist_name'], reply_to_message_id=message_id
                    )
            elif user.database.menu == 21:
                if text == 'افزودن ویس ⏬':
                    user.database.menu = 22
                    user.database.back_menu = 'manage_playlist'
                    await user.send_message(translations.user_messages['send_private_voice'], keyboards.per_back)
                elif text == 'حذف پلی لیست ❌':
                    await user.delete_playlist()
                    await user.send_message(
                        translations.user_messages['playlist_deleted'], reply_to_message_id=message_id
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
                            translations.user_messages['empty_playlist'], reply_to_message_id=message_id
                        )
                elif text == 'لینک دعوت 🔗':
                    await user.send_message(translations.user_messages['playlist_link'].format(
                        await user.playlist_name, await user.playlist_link
                    ))
                elif text == 'مشترکین پلی لیست 👥':
                    await user.send_message(
                        translations.user_messages['playlist_users_count'].format(await user.playlist_users)
                    )
                else:
                    await user.send_message(translations.user_messages['unknown_command'])
            elif user.database.menu == 22:
                if await user.voice_exists(message):
                    if await user.add_voice_to_playlist(message['voice']['file_unique_id']):
                        await user.send_message(translations.user_messages['added_to_playlist'])
                        await user.go_back()
                    else:
                        await user.send_message(
                            translations.user_messages['voice_is_not_yours'], reply_to_message_id=message_id
                        )
            elif user.database.menu == 23:
                if text == 'حذف ویس ❌':
                    if await user.remove_voice_from_playlist():
                        await user.send_message(translations.user_messages['deleted_from_playlist'])
                    else:
                        await user.send_message(translations.user_messages['not_in_playlist'])
                    await user.go_back()
                elif text == 'گوش دادن به ویس 🎧':
                    file_id, name = await user.voice_info
                    await user.send_voice(file_id, name)
                else:
                    await user.send_message(translations.user_messages['unknown_command'])
        await user.save()
    return HttpResponse(status=200)


async def webhook_wrapper(request):
    async with ClientSession() as http_session:
        request.http_session = http_session
        return await webhook(request)
