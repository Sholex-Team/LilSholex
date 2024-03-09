from django.conf import settings
from LilSholex.exceptions import RequestInterruption
from persianmeme.classes import User
from persianmeme.functions import answer_inline_query
from persianmeme.models import User as UserClass
from json import dumps


def handler(request, inline_query, user_chat_id):
    query = inline_query['query']
    offset = inline_query['offset']
    inline_query_id = inline_query['id']
    user = User(request.http_session, user_chat_id)
    user.upload_voice()
    if not user.database.started:
        user.database.save(update_fields=('last_usage_date',))
        answer_inline_query(
            inline_query_id,
            str(),
            str(),
            user.translate('start_the_bot'),
            'new_user',
            request.http_session
        )
        raise RequestInterruption()
    user.set_username()
    user.database.save(update_fields=('last_usage_date', 'started', 'last_start'))
    if user.database.status != UserClass.Status.FULL_BANNED:
        if len((splinted_query := query.split(settings.SEARCH_CAPTION_KEY, 1))) == 2:
            query, caption = splinted_query
        elif query.startswith(settings.EMPTY_CAPTION_KEY):
            caption = query.removeprefix(settings.EMPTY_CAPTION_KEY)
            query = str()
        else:
            caption = None
        results, next_offset = user.get_memes(query, offset, caption)
        answer_inline_query(
            inline_query_id,
            dumps(results),
            next_offset,
            user.translate('add_meme'),
            'suggest_meme',
            request.http_session
        )
