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
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context
from LilSholex.functions import answer_callback_query
from persianmeme import context as meme_context


async def handler():
    callback_query = telegram_context.callback_query.CALLBACK_QUERY.get()
    if callback_query['data'] == 'none':
        raise RequestInterruption()
    inliner = classes.User()
    telegram_context.callback_query.QUERY_ID.set(callback_query['id'])
    await inliner.set_database_instance()
    await inliner.upload_voice()
    if not inliner.database.started:
        async with TaskGroup() as tg:
            tg.create_task(answer_callback_query(inliner.translate('start_to_use'), True))
            tg.create_task(inliner.database.asave())
        raise RequestInterruption()
    try:
        message = callback_query['message']
    except KeyError:
        message_id = None
    else:
        message_id = message['message_id']
    telegram_context.common.USER.set(inliner)
    telegram_context.common.MESSAGE_ID.set(message_id)
    match callback_query['data'].split(':'):
        case ('back', ):
            await inliner.go_back()
        case ('p', chat_id):
            telegram_context.common.CHAT_ID.set(chat_id)
            await user_profile.handler()
        case (('a' | 'd' | 're') as vote_option, meme_id):
            meme_context.callback_query.VOTE_OPTION.set(vote_option)
            meme_context.common.MEME_ID.set(meme_id)
            await voting.handler()
        case (('up' | 'down') as rate_option, meme_id):
            meme_context.callback_query.RATE_OPTION.set(rate_option)
            meme_context.common.MEME_ID.set(meme_id)
            await rating.handler()
        case ('rep', meme_id):
            meme_context.common.MEME_ID.set(meme_id)
            await reporting.handler()
        case (ObjectType.PLAYLIST.value, playlist_id):
            meme_context.common.PLAYLIST_ID.set(playlist_id)
            await playlist.handler()
        case ((
              ObjectType.PRIVATE_VOICE.value |
              ObjectType.SUGGESTED_VOICE.value |
              ObjectType.PLAYLIST_VOICE.value |
              ObjectType.SUGGESTED_VIDEO.value
              ) as callback_type, meme_id):
            meme_context.callback_query.CALLBACK_TYPE.set(callback_type)
            meme_context.common.MEME_ID.set(meme_id)
            await object_types.handler()
        case (page_type, page_str) if page_type.endswith('page'):
            meme_context.callback_query.PAGE_TYPE.set(ObjectType(page_type.removesuffix('page')))
            meme_context.callback_query.PAGE.set(int(page_str))
            await pages.handler()
        case ('r' | 'rd' as command, meme_id):
            meme_context.common.MEME_ID.set(meme_id)
            meme_context.callback_query.COMMAND.set(command)
            if inliner.database.rank in HIGH_LEVEL_ADMINS:
                await delete_logs.handler()
        case (('rep_accept' | 'rep_dismiss') as command, meme_id):
            if inliner.database.rank != User.Rank.USER:
                try:
                    report = await Report.objects.select_related('meme__sender').aget(
                        meme__id=meme_id, status=Report.Status.PENDING
                    )
                except Report.DoesNotExist:
                    async with TaskGroup() as tg:
                        tg.create_task(answer_callback_query(admin_messages['meme_already_processed'], False))
                        tg.create_task(functions.edit_message_reply_markup(settings.MEME_REPORTS_CHANNEL, processed))
                        tg.create_task(inliner.database.asave())
                    raise RequestInterruption()
                finally:
                    await inliner.unpin_chat_message(settings.MEME_REPORTS_CHANNEL)
                meme_context.callback_query.COMMAND.set(command)
                meme_context.common.REPORT.set(report)
                await reports.handler()
        case (command, target_id) if inliner.database.rank == User.Rank.OWNER:
            meme_context.callback_query.COMMAND.set(command)
            match command:
                case 'read' | 'ban' | 'reply':
                    meme_context.callback_query.MESSAGE_ID.set(target_id)
                    await messages.handler()
                case 'delete' | 'delete_deny':
                    meme_context.callback_query.DELETE_REQUEST_ID.set(target_id)
                    await delete_requests.handler()
    await inliner.database.asave()
