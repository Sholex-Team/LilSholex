from persianmeme.classes import User
from persianmeme import translations
from persianmeme.functions import get_delete
from LilSholex.exceptions import RequestInterruption


def handler(command: str, target_id: int, message_id: int, query_id: str, answer_query, inliner: User):
    if not (target_delete := get_delete(target_id)):
        raise RequestInterruption()
    user = User(inliner.session, instance=target_delete.user)
    if command == 'delete':
        target_delete.meme.delete()
        answer_query(query_id, translations.admin_messages['deleted'], True)
        user.send_message(translations.user_messages['deleted'].format(
            translations.user_messages[target_delete.meme.type_string]
        ))
    else:
        target_delete.delete()
        answer_query(query_id, translations.admin_messages['denied'], False)
        user.send_message(translations.user_messages['delete_denied'])
    inliner.delete_message(message_id)
