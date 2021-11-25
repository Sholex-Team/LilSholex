from persianmeme.functions import check_for_voice, check_for_video
from persianmeme.keyboards import admin
from persianmeme.models import MemeType, User
from persianmeme.classes import User as UserClass


def handler(message: dict, user: UserClass, message_id: int):
    if matched := check_for_voice(message):
        user.delete_meme(message['voice']['file_unique_id'], MemeType.VOICE)
    elif matched := check_for_video(message):
        user.delete_meme(message['video']['file_unique_id'], MemeType.VIDEO)
    if matched:
        user.database.menu = User.Menu.ADMIN_MAIN
        user.send_message(user.translate('deleted'), admin)
    else:
        user.send_message(user.translate('unknown_meme'), reply_to_message_id=message_id)
