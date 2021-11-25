from persianmeme.classes import User as UserClass
from persianmeme.models import User
from persianmeme.types import ReportResult
from persianmeme.translations import user_messages
from persianmeme.keyboards import user as user_keyboard


def handler(message: dict, message_id: int, user: UserClass):
    if not (meme := user.get_public_meme(message)):
        return
    match user.report_meme(meme):
        case ReportResult.REPORTED:
            user.database.menu = User.Menu.USER_MAIN
            user.send_message(user_messages['report_submitted'], user_keyboard, message_id)
        case ReportResult.REPORTED_BEFORE:
            user.send_message(user_messages['reported_before'].format(user_messages[meme.type_string]))
        case ReportResult.REPORT_FAILED:
            user.send_message(user_messages['report_reviewed'].format(user_messages[meme.type_string]))
