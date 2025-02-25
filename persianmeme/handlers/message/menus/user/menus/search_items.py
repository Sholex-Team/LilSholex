from persianmeme.classes import User as UserClass
from persianmeme.models import User
from persianmeme.translations import user_messages
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    message_id: int = telegram_context.common.MESSAGE_ID.get()
    matched = True
    async with TaskGroup() as tg:
        match telegram_context.message.TEXT.get():
            case 'ویس ها 🔊':
                user.database.search_items = User.SearchItems.VOICES
                tg.create_task(user.send_message(user_messages['search_item_voices'], reply_to_message_id=message_id))
            case 'ویدئو ها 📹':
                user.database.search_items = User.SearchItems.VIDEOS
                tg.create_task(user.send_message(user_messages['search_item_videos'], reply_to_message_id=message_id))
            case 'ویس ها 🔊 و ویدئو ها 📹':
                user.database.search_items = User.SearchItems.BOTH
                tg.create_task(user.send_message(
                    user_messages['search_item_videos_and_voices'], reply_to_message_id=message_id
                ))
            case _:
                matched = False
                tg.create_task(user.send_message(user_messages['unknown_command'], reply_to_message_id=message_id))
        if matched:
            tg.create_task(user.go_back())
