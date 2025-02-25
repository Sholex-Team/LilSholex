from persianmeme.translations import admin_messages
from persianmeme.keyboards import admin
from asyncio import TaskGroup
from LilSholex.context.telegram import common as common_context
from LilSholex.functions import answer_callback_query


async def handler():
    async with TaskGroup() as tg:
        tg.create_task(common_context.USER.get().send_message(
            admin_messages['user_profile'].format(common_context.CHAT_ID.get()),
            admin,
            parse_mode='Markdown'
        ))
        tg.create_task(answer_callback_query(admin_messages['user_profile_sent'], False))
