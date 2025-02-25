from persianmeme.functions import delete_vote, set_meme_message_id
from django.conf import settings
from LilSholex.context import telegram as telegram_context


async def handler():
    message: dict = telegram_context.message.MESSAGE.get()
    if (str(telegram_context.common.USER_CHAT_ID.get()) == settings.MEME_CHANNEL and (from_user := message.get('from'))
            and from_user['id'] == settings.MEME_ID and (reply_markup := message.get('reply_markup'))):
        if not await set_meme_message_id(
            int(reply_markup['inline_keyboard'][0][0]['callback_data'].split(':')[1]),
            message_id := message['message_id']
        ):
            await delete_vote(message_id)
