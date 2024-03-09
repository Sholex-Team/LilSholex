from persianmeme import models, classes, keyboards
from LilSholex.exceptions import RequestInterruption
from .menus import start, admin_handler, user_handler
from django.utils.html import escape


def handler(request, message: dict, user_chat_id: int):
    if text := message.get('text'):
        text = escape(text)
    message_id = message['message_id']
    user = classes.User(request.http_session, user_chat_id)
    user.set_username()
    user.database.started = True
    if text in ('بازگشت 🔙', 'Back 🔙'):
        user.go_back()
        raise RequestInterruption()
    match user.database:
        case models.User(rank=(
            user.database.Rank.OWNER | user.database.Rank.ADMIN | user.database.Rank.KHIAR
        )) if text in (switch_options := ('/admin', '/user')):
            if text == switch_options[0]:
                user.menu_cleanup()
                user.database.menu_mode = user.database.MenuMode.ADMIN
                user.database.menu = models.User.Menu.ADMIN_MAIN
                user.send_message(user.translate('admin_panel'), keyboards.admin, message_id)
                user.database.save()
                raise RequestInterruption()
            else:
                user.menu_cleanup()
                user.database.menu_mode = user.database.MenuMode.USER
                user.database.menu = models.User.Menu.USER_MAIN
                user.send_message(user.translate('user_panel'), keyboards.user, message_id)
                user.database.save()
                raise RequestInterruption()
        case _ if text and text.startswith('/start'):
            start.handler(text, user, message_id)
        case models.User(
            rank=(user.database.Rank.OWNER | user.database.Rank.ADMIN | user.database.Rank.KHIAR),
            menu_mode=user.database.MenuMode.ADMIN
        ):
            admin_handler.handler(message, text, message_id, user)
        case models.User(status=user.database.Status.ACTIVE, rank=models.User.Rank.USER) | \
                models.User(status=models.User.Status.ACTIVE, menu_mode=models.User.MenuMode.USER):
            user_handler.handler(message, text, message_id, user)
    user.database.save()
