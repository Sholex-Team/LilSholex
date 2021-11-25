from persianmeme.models import Meme
from persianmeme.classes import User
from django.db.models import F


def handler(request, chosen_inline_result, user_chat_id):
    try:
        used_meme = Meme.objects.get(id=chosen_inline_result['result_id'])
    except Meme.DoesNotExist:
        pass
    else:
        if (user := User(
                request.http_session, User.Mode.NORMAL, user_chat_id
        )).database.use_recent_memes:
            user.add_recent_meme(used_meme)
        if used_meme.visibility == Meme.Visibility.NORMAL:
            used_meme.usage_count = F('usage_count') + 1
            used_meme.save()
