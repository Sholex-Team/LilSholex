from persianmeme.models import User, Meme
from persianmeme.keyboards import admin
from persianmeme.classes import User as UserClass


def handler(target_vote: Meme, user: UserClass):
    target_vote.delete_vote(user.session)
    target_vote.sender.status = target_vote.sender.Status.BANNED
    target_vote.sender.save()
    target_vote.deny(user.session)
    user.database.menu = User.Menu.ADMIN_MAIN
    user.send_message(user.translate('ban_voted'), admin)
