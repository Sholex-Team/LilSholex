from LilSholex.exceptions import RequestInterruption
from persianmeme.classes import User
from persianmeme.functions import answer_inline_query
from json import dumps


def handler(request, inline_query, user_chat_id):
    query = inline_query['query']
    offset = inline_query['offset']
    inline_query_id = inline_query['id']
    user = User(request.http_session, User.Mode.SEND_AD, user_chat_id)
    user.upload_voice()
    if not user.database.started:
        user.database.save()
        answer_inline_query(
            inline_query_id,
            str(),
            str(),
            user.translate('start_the_bot'),
            'new_user',
            request.http_session
        )
        raise RequestInterruption()
    user.send_ad()
    user.set_username()
    user.database.save()
    if user.database.status != 'f':
        results, next_offset = user.get_memes(query, offset)
        answer_inline_query(
            inline_query_id,
            dumps(results),
            next_offset,
            user.translate('add_meme'),
            'suggest_meme',
            request.http_session
        )
