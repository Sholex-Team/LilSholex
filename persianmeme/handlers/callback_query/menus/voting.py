from persianmeme.models import Meme
from LilSholex.exceptions import RequestInterruption
from persianmeme.classes import User


def handler(vote_option: str, query_id: str, meme_id: int, answer_query, inliner: User):
    try:
        meme = Meme.objects.get(id=meme_id, status=Meme.Status.PENDING)
    except Meme.DoesNotExist:
        raise RequestInterruption()
    match vote_option:
        case 'a':
            if not inliner.like_meme(meme):
                answer_query(query_id, inliner.translate('vote_before', inliner.translate(
                    meme.type_string
                )), True)
            else:
                answer_query(query_id, inliner.translate('voted'), False)
        case 'd':
            if not inliner.dislike_meme(meme):
                answer_query(query_id, inliner.translate('vote_before', inliner.translate(
                    meme.type_string
                )), True)
            else:
                answer_query(query_id, inliner.translate('voted'), False)
        case _:
            answer_query(query_id, inliner.translate(
                'voting_results', meme.accept_vote.count(), meme.deny_vote.count()
            ), True, 180)
