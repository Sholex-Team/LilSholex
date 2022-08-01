from persianmeme.keyboards import trim_voice as trim_voice_keyboard
from persianmeme.models import User, Meme
from persianmeme.classes import User as UserClass


def handler(target_meme: Meme, user: UserClass):
    user.database.menu = User.Menu.USER_TRIM_VOICE_YES_OR_NO
    user.database.last_meme = target_meme
    # target_meme.send_vote(user.session)
    user.send_message(user.translate('want_to_trim_voice'), trim_voice_keyboard)
