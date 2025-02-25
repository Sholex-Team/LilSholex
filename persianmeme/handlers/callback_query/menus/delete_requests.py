from persianmeme.classes import User as UserClass
from persianmeme.models import Delete
from persianmeme import translations
from LilSholex.exceptions import RequestInterruption
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context
from persianmeme import context as meme_context
from LilSholex.functions import answer_callback_query


async def handler():
    inliner: UserClass = telegram_context.common.USER.get()
    await inliner.delete_message()
    try:
        target_delete = await Delete.objects.select_related('user', 'meme').aget(
            id=meme_context.callback_query.DELETE_REQUEST_ID.get()
        )
    except Delete.DoesNotExist:
        raise RequestInterruption()
    user = UserClass(instance=target_delete.user)
    async with TaskGroup() as tg:
        if meme_context.callback_query.COMMAND.get() == 'delete':
            tg.create_task(target_delete.meme.adelete())
            tg.create_task(answer_callback_query(translations.admin_messages['deleted'], True))
            tg.create_task(user.send_message(translations.user_messages['deleted'].format(
                translations.user_messages[target_delete.meme.type_string]
            )))
        else:
            tg.create_task(target_delete.adelete())
            tg.create_task(answer_callback_query(translations.admin_messages['denied'], False))
            tg.create_task(user.send_message(translations.user_messages['delete_denied']))