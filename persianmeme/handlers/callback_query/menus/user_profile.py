from persianmeme.translations import admin_messages
from persianmeme.keyboards import admin
from persianmeme.classes import User


def handler(chat_id: int, query_id: str, answer_query, inliner: User):
    inliner.send_message(
        admin_messages['user_profile'].format(chat_id),
        admin,
        parse_mode='Markdown'
    )
    answer_query(query_id, admin_messages['user_profile_sent'], False)
