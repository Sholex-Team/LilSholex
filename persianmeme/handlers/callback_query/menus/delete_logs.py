from django.conf import settings
from persianmeme.functions import edit_message_reply_markup
from persianmeme.models import Meme
from LilSholex.exceptions import RequestInterruption
from persianmeme.classes import User
from persianmeme.keyboards import deleted, recovered
from persianmeme import translations
from asyncio import TaskGroup
from persianmeme import context as meme_context
from LilSholex.functions import answer_callback_query


async def handler():
    try:
        deleted_meme = await Meme.objects.select_related('review_admin', 'sender').aget(
            id=meme_context.common.MEME_ID.get(), status=Meme.Status.DELETED
        )
    except Meme.DoesNotExist:
        raise RequestInterruption()
    user = User(instance=deleted_meme.sender)
    async with TaskGroup() as tg:
        if meme_context.callback_query.COMMAND.get() == 'r':
            deleted_meme.status = Meme.Status.ACTIVE
            review_admin = User(instance=deleted_meme.review_admin)
            deleted_meme.review_admin = None
            tg.create_task(deleted_meme.asave())
            tg.create_task(review_admin.send_message(review_admin.translate(
                'deleted_meme_recovered',
                review_admin.translate(deleted_meme.type_string),
                deleted_meme.name
            ), parse_mode='HTML'))
            tg.create_task(answer_callback_query(translations.admin_messages['meme_recovered'].format(
                translations.admin_messages[deleted_meme.type_string]
            ), True))
            tg.create_task(edit_message_reply_markup(settings.MEME_LOGS, recovered))
        else:
            tg.create_task(deleted_meme.adelete())
            tg.create_task(user.send_message(translations.user_messages['deleted_by_admins'].format(
                translations.user_messages[deleted_meme.type_string], deleted_meme.name
            )))
            tg.create_task(edit_message_reply_markup(settings.MEME_LOGS, deleted))
