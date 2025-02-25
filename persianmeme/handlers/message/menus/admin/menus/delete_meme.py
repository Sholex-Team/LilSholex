from persianmeme.functions import check_for_voice, check_for_video
from persianmeme.keyboards import admin
from persianmeme.models import MemeType, User
from persianmeme.classes import User as UserClass
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    async with TaskGroup() as tg:
        if check_for_voice():
            tg.create_task(
                user.delete_meme(telegram_context.message.MESSAGE.get()['voice']['file_unique_id'], MemeType.VOICE)
            )
        elif check_for_video(True):
            tg.create_task(
                user.delete_meme(telegram_context.message.MESSAGE.get()['video']['file_unique_id'], MemeType.VIDEO)
            )
        else:
            await user.send_message(
                user.translate('unknown_meme'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
            )
            return
        user.database.menu = User.Menu.ADMIN_MAIN
        tg.create_task(user.send_message(user.translate('deleted'), admin))
