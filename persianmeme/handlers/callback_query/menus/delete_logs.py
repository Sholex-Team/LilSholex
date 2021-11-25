from django.conf import settings
from persianmeme.functions import edit_message_reply_markup
from persianmeme.models import Meme
from LilSholex.exceptions import RequestInterruption
from persianmeme.classes import User
from persianmeme.keyboards import deleted, recovered
from persianmeme import translations


def handler(command: str, meme_id: int, message_id: int, query_id: str, answer_query, inliner: User):
    try:
        deleted_meme = Meme.objects.get(
            id=meme_id, status=Meme.Status.DELETED
        )
    except Meme.DoesNotExist:
        raise RequestInterruption()
    user = User(inliner.session, User.Mode.NORMAL, instance=deleted_meme.sender)
    if command == 'r':
        deleted_meme.status = Meme.Status.ACTIVE
        assigned_admin = User(inliner.session, User.Mode.NORMAL, instance=deleted_meme.assigned_admin)
        deleted_meme.assigned_admin = None
        deleted_meme.save()
        assigned_admin.send_message(assigned_admin.translate(
            'deleted_meme_recovered',
            assigned_admin.translate(deleted_meme.type_string),
            deleted_meme.name
        ), parse_mode='HTML')
        answer_query(query_id, translations.admin_messages['meme_recovered'].format(
            translations.admin_messages[deleted_meme.type_string]
        ), True)
        edit_message_reply_markup(settings.MEME_LOGS, recovered, message_id=message_id, session=inliner.session)
    else:
        deleted_meme.delete()
        user.send_message(translations.user_messages['deleted_by_admins'].format(
            translations.user_messages[deleted_meme.type_string], deleted_meme.name
        ))
        edit_message_reply_markup(settings.MEME_LOGS, deleted, message_id=message_id, session=inliner.session)
