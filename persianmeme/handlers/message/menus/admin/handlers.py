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
    edit_meme_file,
    meme_review_type
)
from LilSholex.context import telegram as telegram_context
from persianmeme import context as meme_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match user.database.menu:
        case User.Menu.ADMIN_MAIN:
            await main.handler()
        case User.Menu.ADMIN_MEME_NAME:
            if await user.validate_meme_name(user.database.temp_meme_type):
                await meme_name.handler()
        case User.Menu.ADMIN_MEME_TAGS:
            if await user.process_meme_tags():
                await meme_tags.handler()
        case User.Menu.ADMIN_NEW_MEME:
            await new_meme.handler()
        case User.Menu.ADMIN_DELETE_MEME:
            await delete_meme.handler()
        case User.Menu.ADMIN_BAN_USER:
            await ban_user.handler(User.Status.BANNED)
        case User.Menu.ADMIN_UNBAN_USER:
            await ban_user.handler(User.Status.ACTIVE)
        case User.Menu.ADMIN_FULL_BAN_USER:
            await ban_user.handler(User.Status.FULL_BANNED)
        case User.Menu.ADMIN_MESSAGE_USER_ID:
            await message_user_id.handler()
        case User.Menu.ADMIN_MESSAGE_USER:
            await message_user.handler()
        case User.Menu.ADMIN_GET_USER:
            await get_user.handler()
        case User.Menu.ADMIN_BROADCAST:
            await broadcast.handler()
        case User.Menu.ADMIN_BAN_VOTE:
            if target_vote := await user.get_vote():
                meme_context.common.MEME.set(target_vote)
                await ban_vote.handler()
        case User.Menu.ADMIN_SEND_EDIT_MEME:
            if target_meme := await user.get_public_meme():
                meme_context.common.MEME.set(target_meme)
                await send_edit_meme.handler()
        case User.Menu.ADMIN_EDIT_MEME:
            if await user.check_current_meme():
                await edit_meme.handler()
        case User.Menu.ADMIN_EDIT_MEME_NAME:
            if await user.check_current_meme() and await user.validate_meme_name(user.database.current_meme.type):
                await edit_meme_name.handler()
        case User.Menu.ADMIN_EDIT_MEME_TAGS:
            if await user.process_meme_tags():
                await edit_meme_tags.handler()
        case User.Menu.ADMIN_EDIT_MEME_TAGS_AND_DESCRIPTION:
            if await user.process_meme_tags():
                await edit_meme_tags_and_description.handler()
        case User.Menu.ADMIN_EDIT_MEME_DESCRIPTION:
            if await user.check_current_meme() and await user.validate_meme_description():
                await edit_meme_description.handler()
        case User.Menu.ADMIN_EDIT_MEME_FILE:
            if await user.check_current_meme():
                await edit_meme_file.handler()
        case User.Menu.ADMIN_FILE_ID:
            await file_id.handler()
        case User.Menu.ADMIN_MEME_REVIEW_TYPE:
            await meme_review_type.handler()
        case User.Menu.ADMIN_MEME_REVIEW:
            if await user.check_current_meme():
                await meme_review.handler()
        case User.Menu.ADMIN_BROADCAST_STATUS:
            await broadcast_status.handler()
        case User.Menu.ADMIN_MEME_TYPE:
            await meme_type.handler()
