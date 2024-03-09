from persianmeme.models import Meme, ADMINS, User
from LilSholex.exceptions import RequestInterruption
from persianmeme.translations import admin_messages
from persianmeme.classes import User as UserClass


def handler(vote_option: str, query_id: str, meme_id: int, answer_query, inliner: UserClass):
    try:
        meme = Meme.objects.get(id=meme_id, status=Meme.Status.PENDING)
    except Meme.DoesNotExist:
        raise RequestInterruption()
    match vote_option:
        case 'a':
            if inliner.database.rank in ADMINS and inliner.database.menu == User.Menu.ADMIN_GOD_MODE:
                answer_query(
                    query_id, admin_messages['admin_meme_accepted'].format(admin_messages[meme.type_string]), True
                )
                meme.accept(inliner.session)
            elif not inliner.like_meme(meme):
                answer_query(query_id, inliner.translate('vote_before', inliner.translate(
                    meme.type_string
                )), True)
            else:
                answer_query(query_id, inliner.translate('voted'), False)
        case 'd':
            if inliner.database.rank in ADMINS and inliner.database.menu == User.Menu.ADMIN_GOD_MODE:
                answer_query(
                    query_id, admin_messages['admin_meme_denied'].format(admin_messages[meme.type_string]), True
                )
                meme.deny(inliner.session)
            elif not inliner.dislike_meme(meme):
                answer_query(query_id, inliner.translate('vote_before', inliner.translate(
                    meme.type_string
                )), True)
            else:
                answer_query(query_id, inliner.translate('voted'), False)
        case _:
            answer_query(query_id, inliner.translate(
                'voting_results', meme.accept_vote.count(), meme.deny_vote.count()
            ), True, 180)
