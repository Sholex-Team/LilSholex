from django.conf import settings
from LilSholex.exceptions import RequestInterruption
from persianmeme.classes import User
from persianmeme.functions import answer_inline_query
from persianmeme.models import User as UserClass
from json import dumps
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    inline_query = telegram_context.inline_query.INLINE_QUERY.get()
    query = inline_query['query']
    offset = inline_query['offset']
    telegram_context.inline_query.QUERY_ID.set(inline_query['id'])
    user = User()
    await user.set_database_instance()
    await user.upload_voice()
    if not user.database.started:
        async with TaskGroup() as tg:
            tg.create_task(user.database.asave(update_fields=('last_usage_date',)))
            tg.create_task(answer_inline_query(
                str(),
                str(),
                user.translate('start_the_bot'),
                'new_user'
            ))
        raise RequestInterruption()
    if user.database.status != UserClass.Status.FULL_BANNED:
        if len((splinted_query := query.split(settings.SEARCH_CAPTION_KEY, 1))) == 2:
            query, caption = splinted_query
        elif query.startswith(settings.EMPTY_CAPTION_KEY):
            caption = query.removeprefix(settings.EMPTY_CAPTION_KEY)
            query = str()
        else:
            caption = None
        results, next_offset = await user.get_memes(query, offset, caption)
        async with TaskGroup() as tg:
            tg.create_task(answer_inline_query(
                dumps(results),
                next_offset,
                user.translate('add_meme'),
                'suggest_meme'
            ))
            tg.create_task(user.set_username())
            tg.create_task(user.database.asave(update_fields=('last_usage_date', 'started', 'last_start')))
