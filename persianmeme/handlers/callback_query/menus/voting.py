from persianmeme.models import Meme, ADMINS, User
from LilSholex.exceptions import RequestInterruption
from persianmeme.translations import admin_messages
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context
from persianmeme import context as meme_context
from LilSholex.functions import answer_callback_query


async def handler():
    try:
        meme = await Meme.objects.select_related('sender').aget(
            id=meme_context.common.MEME_ID.get(), status=Meme.Status.PENDING
        )
    except Meme.DoesNotExist:
        raise RequestInterruption()
    inliner = telegram_context.common.USER.get()
    match meme_context.callback_query.VOTE_OPTION.get():
        case 'a':
            if inliner.database.rank in ADMINS and inliner.database.menu == User.Menu.ADMIN_GOD_MODE:
                async with TaskGroup() as tg:
                    tg.create_task(answer_callback_query(
                        admin_messages['admin_meme_accepted'].format(admin_messages[meme.type_string]),
                        True
                    ))
                    tg.create_task(meme.accept())
            elif not await inliner.like_meme(meme):
                await answer_callback_query(
                    inliner.translate('vote_before', inliner.translate(meme.type_string)),
                    True
                )
            else:
                await answer_callback_query(inliner.translate('voted'), False)
        case 'd':
            if inliner.database.rank in ADMINS and inliner.database.menu == User.Menu.ADMIN_GOD_MODE:
                async with TaskGroup() as tg:
                    tg.create_task(answer_callback_query(
                        admin_messages['admin_meme_denied'].format(admin_messages[meme.type_string]),
                        True
                    ))
                    tg.create_task(meme.deny())
            elif not await inliner.dislike_meme(meme):
                await answer_callback_query(
                    inliner.translate('vote_before', inliner.translate(meme.type_string)),
                    True
                )
            else:
                await answer_callback_query(inliner.translate('voted'), False)
        case _:
            async with TaskGroup() as tg:
                accept_count = tg.create_task(meme.accept_vote.acount())
                deny_count = tg.create_task(meme.deny_vote.acount())
            await answer_callback_query(inliner.translate(
                'voting_results', accept_count.result(), deny_count.result()
            ), True, 180)
