from persianmeme.classes import User as UserClass
from persianmeme.models import User
from persianmeme.translations import user_messages


def handler(text: str, message_id: int, user: UserClass):
    matched = True
    match text:
        case 'ویس ها 🔊':
            user.database.search_items = User.SearchItems.VOICES
            user.send_message(user_messages['search_item_voices'], reply_to_message_id=message_id)
        case 'ویدئو ها 📹':
            user.database.search_items = User.SearchItems.VIDEOS
            user.send_message(user_messages['search_item_videos'], reply_to_message_id=message_id)
        case 'ویس ها 🔊 و ویدئو ها 📹':
            user.database.search_items = User.SearchItems.BOTH
            user.send_message(user_messages['search_item_videos_and_voices'], reply_to_message_id=message_id)
        case _:
            matched = False
            user.send_message(user_messages['unknown_command'], reply_to_message_id=message_id)
    if matched:
        user.go_back()
