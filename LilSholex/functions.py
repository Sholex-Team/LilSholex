from requests import Session
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


def answer_callback_query(session: Session, token: str):
    def answer_query(query_id, text, show_alert):
        with session.get(
            f'https://api.telegram.org/bot{token}/answerCallbackQuery',
            params={'callback_query_id': query_id, 'text': text, 'show_alert': show_alert}
        ) as _:
            return
    return answer_query


def emoji_number(string_number: str):
    string = str()
    for digit in string_number:
        string += numbers[digit]
    return string
