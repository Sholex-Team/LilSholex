from persianmeme.models import Meme
from persianmeme.classes import User
from LilSholex.exceptions import RequestInterruption
from django.db.models import F


def handler(rate_option: str, meme_id: id, query_id: str, answer_query, inliner: User):
    try:
        meme = Meme.objects.get(id=meme_id)
    except (Meme.DoesNotExist, ValueError):
        inliner.database.save()
        raise RequestInterruption()
    if rate_option == 'up':
        if meme.voters.filter(user_id=inliner.database.user_id).exists():
            answer_query(query_id, inliner.translate(
                'voted_before', inliner.translate(meme.type_string)
            ), True)
        else:
            inliner.add_voter(meme)
            meme.votes = F('votes') + 1
            meme.save()
            answer_query(query_id, inliner.translate(
                'meme_voted', inliner.translate(meme.type_string)
            ), False)
    else:
        if meme.voters.filter(user_id=inliner.database.user_id).exists():
            inliner.remove_voter(meme)
            meme.votes = F('votes') - 1
            meme.save()
            answer_query(query_id, inliner.translate('took_vote_back'), False)
        else:
            answer_query(query_id, inliner.translate('not_voted'), True)
