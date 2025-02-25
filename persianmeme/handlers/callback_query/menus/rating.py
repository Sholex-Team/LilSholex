from persianmeme.models import Meme
from LilSholex.exceptions import RequestInterruption
from django.db.models import F
from persianmeme.translations import user_messages
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context
from persianmeme import context as meme_context
from LilSholex.functions import answer_callback_query


async def handler():
    try:
        meme = await Meme.objects.aget(newmeme_ptr_id=meme_context.common.MEME_ID.get())
    except (Meme.DoesNotExist, ValueError):
        await telegram_context.common.USER.get().database.asave()
        raise RequestInterruption()
    if meme_context.callback_query.RATE_OPTION.get() == 'up':
        if await meme.voters.acontains(telegram_context.common.USER.get().database):
            await answer_callback_query(
                user_messages['voted_before'].format(user_messages[meme.type_string]), True
            )
        else:
            meme.votes = F('votes') + 1
            async with TaskGroup() as tg:
                tg.create_task(telegram_context.common.USER.get().add_voter(meme))
                tg.create_task(meme.asave(update_fields=('votes',)))
                tg.create_task(answer_callback_query(
                    user_messages['meme_voted'].format(user_messages[meme.type_string]), False
                ))
    else:
        if await meme.voters.acontains((inliner := telegram_context.common.USER.get()).database):
            meme.votes = F('votes') - 1
            async with TaskGroup() as tg:
                tg.create_task(inliner.remove_voter(meme))
                tg.create_task(meme.asave())
                tg.create_task(answer_callback_query(user_messages['took_vote_back'], False))
        else:
            await answer_callback_query(user_messages['not_voted'], True)
