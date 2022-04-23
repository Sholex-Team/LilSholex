from persianmeme import functions, keyboards
from persianmeme.classes import User as UserClass
from persianmeme.models import User, BOT_ADMINS, Delete
from persianmeme.translations import admin_messages


def handler(message: dict, text: str, user: UserClass, message_id: int):
    user.database.back_menu = 'main'
    not_matched = False
    match text:
        case 'Add Meme':
            user.database.menu = User.Menu.ADMIN_MEME_TYPE
            user.send_message(admin_messages['meme_type'], keyboards.en_meme_type)
        case 'Meme Count':
            user.send_message(functions.count_memes())
        case 'Member Count':
            user.send_message(user.translate('member_count', User.objects.count()))
        case _:
            if (search_result := user.get_public_meme(message)) is False:
                not_matched = True
            elif search_result:
                user.send_message(
                    user.translate(
                        'meme_info', user.translate(search_result.type_string), search_result.name
                    ),
                    keyboards.use(search_result.id)
                )
    if not_matched and user.database.rank in BOT_ADMINS:
        match text:
            case 'Get User':
                user.database.menu = User.Menu.ADMIN_GET_USER
                user.send_message(admin_messages['chat_id'], keyboards.en_back)
            case 'Ban a User':
                user.database.menu = User.Menu.ADMIN_BAN_USER
                user.send_message(admin_messages['chat_id'], keyboards.en_back)
            case 'Unban a User':
                user.database.menu = User.Menu.ADMIN_UNBAN_USER
                user.send_message(admin_messages['chat_id'], keyboards.en_back)
            case 'Full Ban':
                user.database.menu = User.Menu.ADMIN_FULL_BAN_USER
                user.send_message(admin_messages['chat_id'], keyboards.en_back)
            case 'Delete Meme':
                user.database.menu = User.Menu.ADMIN_DELETE_MEME
                user.send_message(admin_messages['meme'], keyboards.en_back)
            case 'Ban Vote':
                user.database.menu = User.Menu.ADMIN_BAN_VOTE
                user.send_message(admin_messages['meme'], keyboards.en_back)
            case 'Edit Meme':
                user.database.menu = User.Menu.ADMIN_SEND_EDIT_MEME
                user.send_message(
                    admin_messages['send_edit_meme'], keyboards.en_back
                )
            case 'File ID':
                user.database.menu = User.Menu.ADMIN_FILE_ID
                user.send_message(admin_messages['send_document'], keyboards.en_back)
            case 'Meme Review' if user.assign_meme():
                user.database.menu = User.Menu.ADMIN_MEME_REVIEW
            case 'God Mode':
                user.database.menu = User.Menu.ADMIN_GOD_MODE
                user.send_message(admin_messages['god_mode'], keyboards.en_back, message_id)
            case _ if user.database.rank == user.database.Rank.OWNER:
                match text:
                    case 'Message User':
                        user.database.menu = User.Menu.ADMIN_MESSAGE_USER_ID
                        user.send_message(admin_messages['chat_id'], keyboards.en_back)
                    case 'Add Ad':
                        user.database.menu = User.Menu.ADMIN_ADD_AD
                        user.send_message(admin_messages['send_ad'], keyboards.en_back)
                    case 'Delete Ad':
                        user.database.menu = User.Menu.ADMIN_DELETE_AD
                        user.send_message(admin_messages['send_ad_id'], keyboards.en_back)
                    case 'Delete Requests':
                        if (delete_requests := Delete.objects.all()).exists():
                            for delete_request in delete_requests:
                                delete_request.meme.send_meme(
                                    user.database.chat_id,
                                    user.session,
                                    keyboards.delete_voice(delete_request.id),
                                    f'<b>From</b>: <code>{delete_request.user.chat_id}</code>\n\n'
                                )
                            user.send_message(
                                admin_messages['delete_requests'],
                                reply_to_message_id=message_id
                            )
                        else:
                            user.send_message(
                                admin_messages['no_delete_requests'],
                                reply_to_message_id=message_id
                            )
                    case 'Broadcast':
                        user.database.menu = User.Menu.ADMIN_BROADCAST
                        user.send_message(admin_messages['broadcast'], keyboards.en_back)
                    case 'Edit Ad':
                        user.database.menu = User.Menu.ADMIN_EDIT_AD_ID
                        user.send_message(admin_messages['edit_ad'], keyboards.en_back)
                    case 'Messages':
                        user.send_messages()
                    case 'Started Count':
                        user.send_message(user.translate(
                            'started_count',
                            User.objects.filter(
                                started=True, status=User.Status.ACTIVE
                            ).count()
                        ), reply_to_message_id=message_id)
                    case 'Broadcast Status':
                        user.database.menu = User.Menu.ADMIN_BROADCAST_STATUS
                        user.send_message(admin_messages['broadcast_id'], keyboards.en_back)
