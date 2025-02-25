from persianmeme.models import NewMeme
from persianmeme.classes import User
from django.db.models import F
from asyncio import TaskGroup
from LilSholex.context.telegram import chosen_inline_result as chosen_inline_result_context


async def handler():
    try:
        used_meme = await NewMeme.objects.aget(id=chosen_inline_result_context.CHOSEN_INLINE_RESULT.get()['result_id'])
    except NewMeme.DoesNotExist:
        pass
    else:
        user = User()
        await user.set_database_instance()
        async with TaskGroup() as tg:
            if user.database.use_recent_memes:
                tg.create_task(user.add_recent_meme(used_meme))
            if used_meme.visibility == NewMeme.Visibility.NORMAL:
                used_meme.usage_count = F('usage_count') + 1
                tg.create_task(used_meme.asave(update_fields=('usage_count',)))
