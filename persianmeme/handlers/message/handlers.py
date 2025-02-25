from persianmeme import models, classes, keyboards
from LilSholex.exceptions import RequestInterruption
from .menus import start, admin_handler, user_handler, cancel_voting
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    message = telegram_context.message.MESSAGE.get()
    text = message.get('text')
    message_id = message['message_id']
    telegram_context.common.MESSAGE_ID.set(message_id)
    user = classes.User()
    await user.set_database_instance()
    await user.set_username()
    user.database.started = True
    if text in ('بازگشت 🔙', 'Back 🔙'):
        await user.go_back()
        raise RequestInterruption()
    telegram_context.common.USER.set(user)
    telegram_context.message.TEXT.set(text)
    match user.database:
        case models.User(rank=(
            user.database.Rank.OWNER | user.database.Rank.ADMIN | user.database.Rank.KHIAR
        )) if text in (switch_options := ('/admin', '/user')):
            if text == switch_options[0]:
                user.menu_cleanup()
                user.database.menu_mode = user.database.MenuMode.ADMIN
                user.database.menu = models.User.Menu.ADMIN_MAIN
                async with TaskGroup() as tg:
                    tg.create_task(user.send_message(user.translate('admin_panel'), keyboards.admin, message_id))
                    tg.create_task(user.database.asave())
                raise RequestInterruption()
            else:
                user.menu_cleanup()
                user.database.menu_mode = user.database.MenuMode.USER
                user.database.menu = models.User.Menu.USER_MAIN
                async with TaskGroup() as tg:
                    tg.create_task(user.send_message(user.translate('user_panel'), keyboards.user, message_id))
                    tg.create_task(user.database.asave())
                raise RequestInterruption()
        case _ if text and text.startswith('/start'):
            await start.handler()
        case _ if text and text.startswith('/cancelvoting'):
            await cancel_voting.handler()
        case models.User(
            rank=(user.database.Rank.OWNER | user.database.Rank.ADMIN | user.database.Rank.KHIAR),
            menu_mode=user.database.MenuMode.ADMIN
        ):
            await admin_handler.handler()
        case models.User(status=user.database.Status.ACTIVE, rank=models.User.Rank.USER) | \
                models.User(status=models.User.Status.ACTIVE, menu_mode=models.User.MenuMode.USER):
            await user_handler.handler()
    await user.database.asave()
