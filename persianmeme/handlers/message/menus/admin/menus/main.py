from persianmeme import keyboards
from persianmeme.classes import User as UserClass
from persianmeme.models import User, HIGH_LEVEL_ADMINS, Delete, Meme
from persianmeme.translations import admin_messages
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    user.database.back_menu = 'main'
    not_matched = False
    text: str = telegram_context.message.TEXT.get()
    message_id: int = telegram_context.common.MESSAGE_ID.get()
    match text:
        case 'Add Meme':
            user.database.menu = User.Menu.ADMIN_MEME_TYPE
            await user.send_message(admin_messages['meme_type'], keyboards.en_meme_type)
        case 'Meme Count':
            await user.send_message(
                f'All memes count : {await Meme.objects.filter(status=Meme.Status.ACTIVE).acount()}'
            )
        case 'Member Count':
            await user.send_message(user.translate('member_count', await User.objects.acount()))
        case 'God Mode':
            user.database.menu = User.Menu.ADMIN_GOD_MODE
            await user.send_message(admin_messages['god_mode'], keyboards.en_back, message_id)
        case _:
            if (search_result := await user.get_public_meme()) is False:
                not_matched = True
            elif search_result:
                await user.send_message(
                    user.translate(
                        'meme_info', user.translate(search_result.type_string), search_result.name
                    ),
                    keyboards.use(search_result.newmeme_ptr_id),
                    message_id
                )
    if not_matched and user.database.rank in HIGH_LEVEL_ADMINS:
        match text:
            case 'Get User':
                user.database.menu = User.Menu.ADMIN_GET_USER
                await user.send_message(admin_messages['chat_id'], keyboards.en_back)
            case 'Ban a User':
                user.database.menu = User.Menu.ADMIN_BAN_USER
                await user.send_message(admin_messages['chat_id'], keyboards.en_back)
            case 'Unban a User':
                user.database.menu = User.Menu.ADMIN_UNBAN_USER
                await user.send_message(admin_messages['chat_id'], keyboards.en_back)
            case 'Full Ban':
                user.database.menu = User.Menu.ADMIN_FULL_BAN_USER
                await user.send_message(admin_messages['chat_id'], keyboards.en_back)
            case 'Delete Meme':
                user.database.menu = User.Menu.ADMIN_DELETE_MEME
                await user.send_message(admin_messages['meme'], keyboards.en_back)
            case 'Ban Vote':
                user.database.menu = User.Menu.ADMIN_BAN_VOTE
                await user.send_message(admin_messages['meme'], keyboards.en_back)
            case 'Edit Meme':
                user.database.menu = User.Menu.ADMIN_SEND_EDIT_MEME
                await user.send_message(
                    admin_messages['send_edit_meme'], keyboards.en_back
                )
            case 'File ID':
                user.database.menu = User.Menu.ADMIN_FILE_ID
                await user.send_message(admin_messages['send_document'], keyboards.en_back)
            case 'Meme Review':
                user.clear_temp_meme_type()
                user.database.menu = User.Menu.ADMIN_MEME_REVIEW_TYPE
                await user.send_message(
                    admin_messages['meme_review_type'].format(*await user.unreviewed_memes_count),
                    keyboards.meme_review_type,
                    message_id
                )
            case _ if user.database.rank == user.database.Rank.OWNER:
                match text:
                    case 'Message User':
                        user.database.menu = User.Menu.ADMIN_MESSAGE_USER_ID
                        await user.send_message(admin_messages['chat_id'], keyboards.en_back)
                    case 'Delete Requests':
                        if await (delete_requests := Delete.objects.all().select_related('meme', 'user')).aexists():
                            async for delete_request in delete_requests:
                                await delete_request.meme.send_meme(
                                    user.database.chat_id,
                                    keyboards.delete_voice(delete_request.id),
                                    f'<b>From</b>: <code>{delete_request.user.chat_id}</code>\n\n'
                                )
                            await user.send_message(
                                admin_messages['delete_requests'],
                                reply_to_message_id=message_id
                            )
                        else:
                            await user.send_message(
                                admin_messages['no_delete_requests'],
                                reply_to_message_id=message_id
                            )
                    case 'Broadcast':
                        user.database.menu = User.Menu.ADMIN_BROADCAST
                        await user.send_message(admin_messages['broadcast'], keyboards.en_back)
                    case 'Messages':
                        await user.send_messages()
                    case 'Started Count':
                        await user.send_message(user.translate(
                            'started_count',
                            await User.objects.filter(
                                started=True, status=User.Status.ACTIVE
                            ).acount()
                        ), reply_to_message_id=message_id)
                    case 'Broadcast Status':
                        user.database.menu = User.Menu.ADMIN_BROADCAST_STATUS
                        await user.send_message(admin_messages['broadcast_id'], keyboards.en_back)
