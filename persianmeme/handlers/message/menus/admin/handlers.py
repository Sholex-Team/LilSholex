from persianmeme.models import User
from persianmeme.classes import User as UserClass
from .menus import (
    main,
    meme_name,
    delete_meme,
    ban_user,
    message_user_id,
    get_user,
    edit_meme,
    meme_review,
    broadcast_status,
    meme_type,
    meme_tags,
    new_meme,
    message_user,
    broadcast,
    ban_vote,
    send_edit_meme,
    file_id,
    edit_meme_name,
    edit_meme_tags,
    edit_meme_tags_and_description,
    edit_meme_description,
    edit_meme_file
)


def handler(message: dict, text: str, message_id: int, user: UserClass):
    match user.database.menu:
        case User.Menu.ADMIN_MAIN:
            main.handler(message, text, user, message_id)
        case User.Menu.ADMIN_MEME_NAME if text:
            meme_name.handler(message, text, user)
        case User.Menu.ADMIN_MEME_TAGS:
            meme_tags.handler(text, user)
        case User.Menu.ADMIN_NEW_MEME:
            new_meme.handler(message, user)
        case User.Menu.ADMIN_DELETE_MEME:
            delete_meme.handler(message, user, message_id)
        case User.Menu.ADMIN_BAN_USER:
            ban_user.handler(text, user, User.Status.BANNED)
        case User.Menu.ADMIN_UNBAN_USER:
            ban_user.handler(text, user, User.Status.ACTIVE)
        case User.Menu.ADMIN_FULL_BAN_USER:
            ban_user.handler(text, user, User.Status.FULL_BANNED)
        case User.Menu.ADMIN_MESSAGE_USER_ID:
            message_user_id.handler(text, user)
        case User.Menu.ADMIN_MESSAGE_USER:
            message_user.handler(message_id, user)
        case User.Menu.ADMIN_GET_USER:
            get_user.handler(text, user, message_id)
        case User.Menu.ADMIN_BROADCAST:
            broadcast.handler(message_id, user)
        case User.Menu.ADMIN_BAN_VOTE if target_vote := user.get_vote(message):
            ban_vote.handler(target_vote, user)
        case User.Menu.ADMIN_SEND_EDIT_MEME if target_meme := user.get_public_meme(message):
            send_edit_meme.handler(target_meme, user)
        case User.Menu.ADMIN_EDIT_MEME:
            edit_meme.handler(text, message_id, user)
        case User.Menu.ADMIN_EDIT_MEME_NAME if user.validate_meme_name(
                message, text, user.database.current_meme.type
        ):
            edit_meme_name.handler(text, user)
        case User.Menu.ADMIN_EDIT_MEME_TAGS if user.process_meme_tags(text):
            edit_meme_tags.handler(user)
        case User.Menu.ADMIN_EDIT_MEME_TAGS_AND_DESCRIPTION if user.process_meme_tags(text):
            edit_meme_tags_and_description.handler(user)
        case User.Menu.ADMIN_EDIT_MEME_DESCRIPTION if user.validate_meme_description(
                text, message_id, user.database.current_meme.type
        ):
            edit_meme_description.handler(text, user)
        case User.Menu.ADMIN_EDIT_MEME_FILE:
            edit_meme_file.handler(message, user)
        case User.Menu.ADMIN_FILE_ID:
            file_id.handler(message, message_id, user)
        case User.Menu.ADMIN_MEME_REVIEW:
            meme_review.handler(text, message_id, user)
        case User.Menu.ADMIN_BROADCAST_STATUS:
            broadcast_status.handler(text, message_id, user)
        case User.Menu.ADMIN_MEME_TYPE:
            meme_type.handler(text, user)
