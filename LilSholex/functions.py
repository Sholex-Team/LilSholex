from .decorators import async_fix
from .exceptions import TooManyRequests
from aiohttp import ClientResponse
from .context import telegram as telegram_context

numbers = {
    '0': '0️⃣',
    '1': '1️⃣',
    '2': '2️⃣',
    '3': '3️⃣',
    '4': '4️⃣',
    '5': '5️⃣',
    '6': '6️⃣',
    '7': '7️⃣',
    '8': '8️⃣',
    '9': '9️⃣'
}


async def handle_request_exception(response: ClientResponse):
    if response.status != 429:
        return
    raise TooManyRequests((await response.json())['parameters']['retry_after'])


@async_fix
async def answer_callback_query(text: str, show_alert: bool, cache_time: int = 0):
    async with telegram_context.common.HTTP_SESSION.get().get(
        f'https://api.telegram.org/bot{telegram_context.common.BOT_TOKEN.get()}/answerCallbackQuery',
        params={
            'callback_query_id': telegram_context.callback_query.QUERY_ID.get(),
            'text': text,
            'show_alert': str(show_alert),
            'cache_time': cache_time
        }
    ) as response:
        return await handle_request_exception(response)


def emoji_number(string_number: str):
    string = str()
    for digit in string_number:
        string += numbers[digit]
    return string
