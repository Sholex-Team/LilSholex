import json
from support import classes, keyboards, models
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from datetime import datetime


@require_POST
@csrf_exempt
def webhook(request):
    """
    This view function will be used as a webhook .
    """
    update = json.loads(request.body.decode())
    if 'callback_query' in update:
        if len((data := update['callback_query']['data'].split(':'))) == 2:
            admin = classes.User(update['callback_query']['from']['id'])
            if not (message := models.Message.objects.get(message_id=data[0])).admin:
                callback_id = update['callback_query']['id']
                user = classes.User(instance=message.users_message.first())
                message.admin = admin.database
                user.send_message(user.translate('answered'), reply_to_message_id=message.message_unique_id)
                classes.answer_callback_query(callback_id, 'Message has been checked ✔️')
                if data[1] == 'answer':
                    admin.database.current_message = message
                    classes.answer_callback_query(callback_id, 'Answering ⭕️')
                    admin.database.menu = 2
                    admin.database.save()
                    admin.send_message('Please send the answer .', keyboards.en_back)
                elif data[1] in ('ban', 'read'):
                    user.database.current_message = None
                    if data[1] == 'ban':
                        user.database.menu = 1
                        user.database.status = 'b'
                        user.send_message(user.translate('banned'))
                    user.database.save()
                message.save()
            admin.edit_message_reply_markup(update['callback_query']['message']['message_id'], keyboards.seen)
        return HttpResponse(status=200)

    elif 'message' in update:
        message = update['message']
    elif 'edited_message' in update:
        message = update['edited_message']
    else:
        return HttpResponse(status=200)
    text: str = message.get('text', 'None')
    if message['chat']['id'] < 0:  # Get Message on Group
        pass
    else:
        message_id = message['message_id']
        user = classes.User(message['chat']['id'])
        if user.database.rank == 'a':
            if text == '/start':
                user.send_message('Welcome to admin support !', keyboards.admin, message_id)
                user.database.menu = 1
            elif user.database.menu == 1:
                if text == 'Unanswered messages':
                    if (new_messages := models.Message.objects.filter(admin=None)).exists():
                        for message in new_messages:
                            user.send_message(
                                f'New Message from : {message.users_message.all()[0].chat_id}\n'
                                f'Webapp : {message.get_webapp_display()}\n'
                                f'Message Type : {message.get_message_type_display()}\nText : \n{message.text}',
                                keyboards.message(message.message_id)
                            )
                    else:
                        user.send_message('There are no new messages ⚠️', reply_to_message_id=message_id)
            elif user.database.menu == 2:
                user.database.menu = 1
                target_user = classes.User(instance=user.database.current_message.users_message.all()[0])
                target_user.database.current_message.answering_date = datetime.now()
                target_user.database.current_message.save()
                target_user.database.current_message = None
                target_user.database.save()
                if text == 'Back 🔙':
                    user.send_message('You are back at main menu 🔙', keyboards.admin)
                else:
                    target_user.send_message(text, reply_to_message_id=user.database.current_message.message_unique_id)
                    user.send_message('Message has been sent to user ✔️', keyboards.admin)
        elif user.database.status == 'a':
            if text == '/start':
                user.send_message(user.translate('start'), user.get_keyboard('user'), message_id)
                user.database.menu = 1
            elif user.database.menu == 1:
                if text in ('Group Guard', 'مدیریت گروه', 'Anonymous Message', 'پیام ناشناس'):
                    if user.database.current_message:
                        user.send_message(user.translate('exists'), reply_to_message_id=message_id)
                    else:
                        if text in ('Group Guard', 'مدیریت گروه'):
                            user.database.current_webapp = 'g'
                        elif text in ('Anonymous Message', 'پیام ناشناس'):
                            user.database.current_webapp = 'a'
                        else:
                            user.database.current_webapp = 'm'
                        user.database.menu = 2
                        user.send_message(user.translate('type'), user.get_keyboard('type'))
                elif text in ('زبان 📖', 'Language 📖'):
                    user.database.menu = 4
                    user.send_message(user.translate('language'), user.get_keyboard('lang'))
                else:
                    user.send_message(user.translate('unknown_webapp'))
            elif user.database.menu == 2:
                if text in ('Back 🔙', 'بازگشت 🔙'):
                    user.database.menu = 1
                    user.send_message(user.translate('back_main'), user.get_keyboard('user'))
                elif text in ('Suggestion 👌', 'Bug ☢', 'پیشنهادات 👌', 'باگ ☢'):
                    if text in ('باگ ☢', 'Bug ☢'):
                        user.database.current_type = 'b'
                    else:
                        user.database.current_type = 's'
                    user.database.menu = 3
                    user.send_message(user.translate('message'), user.get_keyboard('back'))
                else:
                    user.send_message(user.translate('unknown_type'))
            elif user.database.menu == 3:
                if text in ('Back 🔙', 'بازگشت 🔙'):
                    user.database.menu = 2
                    user.send_message(user.translate('type'), user.get_keyboard('type'))
                else:
                    new_message = models.Message.objects.create(
                        message_unique_id=message_id,
                        webapp=user.database.current_webapp,
                        message_type=user.database.current_type,
                        text=text,
                    )
                    user.database.current_message = new_message
                    for admin in models.User.objects.filter(rank='a'):
                        admin = classes.User(instance=admin)
                        admin.send_message(
                            f'New Message received 📬\nUnanswered messages count : '
                            f'{models.Message.objects.filter(admin=None).count()} !'
                        )
                    user.database.menu = 1
                    user.send_message(user.translate('sent'), user.get_keyboard('user'))
            elif user.database.menu == 4:
                if text in ('بازگشت 🔙', 'Back 🔙'):
                    user.database.menu = 1
                    user.send_message(user.translate('back_main'), user.get_keyboard('user'))
                elif text == 'فارسی 🇮🇷':
                    user.database.lang = 'fa'
                    user.database.menu = 1
                    user.send_message('زبان به فارسی تغییر کرد 🇮🇷', keyboards.fa_user)
                elif text == 'English 🇺🇸':
                    user.database.lang = 'en'
                    user.database.menu = 1
                    user.send_message('Language changed to English 🇺🇸', keyboards.en_user)
                else:
                    user.send_message(user.translate('unknown_lang'), reply_to_message_id=message_id)
        else:
            user.database.menu = 1
            user.send_message(user.translate('banned'), reply_to_message_id=message_id)
        user.database.save()
    return HttpResponse(status=200)
