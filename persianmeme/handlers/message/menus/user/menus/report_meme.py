from persianmeme.classes import User as UserClass
from persianmeme.models import User
from persianmeme.types import ReportResult
from persianmeme.translations import user_messages
from persianmeme.keyboards import user as user_keyboard
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    if not (meme := await user.get_public_meme()):
        return
    match await user.report_meme(meme):
        case ReportResult.REPORTED:
            user.database.menu = User.Menu.USER_MAIN
            await user.send_message(
                user_messages['report_submitted'], user_keyboard, telegram_context.common.MESSAGE_ID.get()
            )
        case ReportResult.REPORTED_BEFORE:
            await user.send_message(user_messages['reported_before'].format(user_messages[meme.type_string]))
        case ReportResult.REPORT_FAILED:
            await user.send_message(user_messages['report_reviewed'].format(user_messages[meme.type_string]))
