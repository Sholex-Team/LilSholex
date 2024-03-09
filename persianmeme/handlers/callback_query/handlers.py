from persianmeme import functions, classes
from LilSholex.exceptions import RequestInterruption
from persianmeme.models import User, Report, HIGH_LEVEL_ADMINS
from persianmeme.types import ObjectType
from .menus import (
    user_profile,
    voting,
    rating,
    reporting,
    playlist,
    object_types,
    pages,
    messages,
    delete_requests,
    delete_logs,
    reports
)
from persianmeme.translations import admin_messages
from persianmeme.keyboards import processed
from django.conf import settings


def handler(request, callback_query, user_chat_id):
    answer_query = functions.answer_callback_query(request.http_session)
    if callback_query['data'] == 'none':
        raise RequestInterruption()
    query_id = callback_query['id']
    inliner = classes.User(request.http_session, user_chat_id)
    inliner.upload_voice()
    if not inliner.database.started:
        answer_query(query_id, inliner.translate('start_to_use'), True)
        inliner.database.save()
        raise RequestInterruption()
    callback_data = callback_query['data'].split(':')
    try:
        message = callback_query['message']
    except KeyError:
        message_id = None
    else:
        message_id = message['message_id']
    match callback_data:
        case ('back', ):
            inliner.go_back()
        case ('p', chat_id):
            user_profile.handler(chat_id, query_id, answer_query, inliner)
        case (('a' | 'd' | 're') as vote_option, meme_id):
            voting.handler(vote_option, query_id, meme_id, answer_query, inliner)
        case (('up' | 'down') as rate_option, meme_id):
            rating.handler(rate_option, meme_id, query_id, answer_query, inliner)
        case ('rep', meme_id):
            reporting.handler(meme_id, query_id, answer_query, inliner)
        case (ObjectType.PLAYLIST.value, playlist_id):
            playlist.handler(playlist_id, query_id, answer_query, inliner)
        case ((
              ObjectType.PRIVATE_VOICE.value |
              ObjectType.SUGGESTED_VOICE.value |
              ObjectType.PLAYLIST_VOICE.value |
              ObjectType.SUGGESTED_VIDEO.value
              ) as callback_type, meme_id):
            object_types.handler(callback_type, meme_id, query_id, answer_query, inliner)
        case (page_type, page_str) if page_type.endswith('page'):
            pages.handler(ObjectType(page_type.removesuffix('page')), int(page_str), message_id, inliner)
        case ('r' | 'rd' as command, meme_id) if inliner.database.rank in HIGH_LEVEL_ADMINS:
            delete_logs.handler(command, meme_id, message_id, query_id, answer_query, inliner)
        case (('rep_accept' | 'rep_dismiss') as command, meme_id) if inliner.database.rank != User.Rank.USER:
            try:
                report = Report.objects.get(meme__id=meme_id, status=Report.Status.PENDING)
            except Report.DoesNotExist:
                answer_query(query_id, admin_messages['meme_already_processed'], False)
                functions.edit_message_reply_markup(
                    settings.MEME_REPORTS_CHANNEL, processed, message_id, session=inliner.session
                )
                inliner.database.save()
                raise RequestInterruption()
            finally:
                inliner.unpin_chat_message(settings.MEME_REPORTS_CHANNEL, message_id)
            reports.handler(command, query_id, message_id, answer_query, report, inliner)
        case (command, target_id) if inliner.database.rank == User.Rank.OWNER:
            match command:
                case 'read' | 'ban' | 'reply':
                    messages.handler(command, target_id, message_id, query_id, answer_query, inliner)
                case 'delete' | 'delete_deny':
                    delete_requests.handler(command, target_id, message_id, query_id, answer_query, inliner)
    inliner.database.save()
