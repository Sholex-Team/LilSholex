import json
from anonymous import classes, keyboards, functions, models
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError


@require_POST
@csrf_exempt
def webhook(request):
    update = json.loads(request.body.decode())
    # Callback Query
    if 'callback_query' in update:
        callback_query = update['callback_query']
        user = classes.User(chat_id=callback_query['from']['id'])
        callback_data = callback_query['data'].split(':')
        try:
            user_in_callback = classes.User(token=callback_data[1])
        except models.User.DoesNotExist:
            pass
        else:
            if callback_data[0] == 'answer':
                if user.database in user_in_callback.database.black_list.all():
                    functions.answer_callback_query(callback_query['id'], 'شما در لیست سیاه کاربر قرار دارید ❌', True)
                else:
                    functions.answer_callback_query(callback_query['id'], 'پیام خوانده شد ✅', False)
                    user.send_message('پیام خود را ارسال کنید.', reply_markup=keyboards.fa_back)
                    user.database.token_last_receiver = callback_data[1]
                    user.database.menu = 5
            elif callback_data[0] == 'block':
                if user_in_callback.database not in user.database.black_list.all():
                    user.database.black_list.add(user_in_callback.database)
                    functions.answer_callback_query(callback_query['id'], 'کاربر در لیست سیاه قرار گرفت. ☠️', True)
                else:
                    functions.answer_callback_query(callback_query['id'], 'کاربر در لیست سیاه قرار دارد !', False)
            elif callback_data[0] == 'unblock':
                user.database.black_list.remove(user_in_callback.database)
                user.send_message(
                    f'کاربر `{user_in_callback.database.nick_name}` از لیست سیاه خارج شد. 🔓', parse_mode='Markdown'
                )
        user.database.save()
        return HttpResponse(status=200)
    # Normal Messages
    elif 'message' in update:
        message = update['message']
    elif 'edited_message' in update:
        message = update['edited_message']
    else:
        return HttpResponse(status=200)
    if (text := message.get('text', 'None')) in ('.', '/'):
        text = 'None'
    message_id = message['message_id']
    # Checking if chat_id belongs to a group
    if message['from']['id'] < 0:
        return HttpResponse(status=200)
    else:
        user = classes.User(message['from']['id'])
        user.database.username = message['from'].get('username', None)
        if user.database.status == 'b':
            if text == 'Support':
                user.send_message('برای تماس با مدیریت از بات زیر استفاده کنید.', reply_markup=keyboards.support_())
            else:
                user.send_message(
                    'شما در ربات بلاک شده اید لطفا به پشتیبانی پیام دهید.', reply_markup=keyboards.support_()
                )
                user.database.menu = 1
                user.database.save()
                return HttpResponse(status=200)
        if user.database.rank == 'a':  # Admin Section
            if text.startswith('/'):  # Command Check
                text = text[1:]
                if (text := text.split())[0] == 'start':
                    if len(text) < 2:
                        if user.database.nick_name:
                            user.send_message(
                                'Welcome to Admin Panel', reply_to_message_id=message_id, reply_markup=keyboards.admin
                            )
                            user.database.menu = 1
                        else:
                            user.send_message('یک نام برای خود تعیین کنید. ✏️\nاین نام برای دیگران قابل نمایش است. 🙊')
                            user.database.menu = 6
                            user.database.last_menu = 0
                    else:
                        try:
                            user_black_list = classes.User(token=text[1]).database.black_list.all()
                        except models.User.DoesNotExist:
                            pass
                        else:
                            if user.database.nick_name:
                                if user.database in user_black_list:
                                    user.send_message(
                                        'شما در لیست سیاه کاربر مورد نظر میباشید. 💀', reply_markup=keyboards.user
                                    )
                                    user.database.menu = 1
                                user.database.token_last_receiver = text[1]
                                user.send_message('پیام خود را ارسال کنید.', reply_markup=keyboards.en_back)
                                user.database.menu = 4
                            else:
                                user.send_message(
                                    'یک نام برای خود تعیین کنید. ✏️\nاین نام برای دیگران قابل نمایش است. 🙊'
                                )
                                user.database.menu = 6
                                user.database.last_menu = 4
            elif user.database.menu == 1:
                if text == 'Users':
                    user.send_message(
                        functions.get_users_count(), reply_to_message_id=message_id, reply_markup=keyboards.admin
                    )
                elif text == 'Ban User':
                    user.send_message(
                        'Please send user id.', reply_to_message_id=message_id, reply_markup=keyboards.en_back
                    )
                    user.database.menu = 2
                elif text == 'Unban User':
                    user.send_message('Please send user id.', reply_to_message_id=message_id,
                                      reply_markup=keyboards.en_back)
                    user.database.menu = 3
                elif text == 'Link':
                    user.send_url()
                elif text == 'NickName':
                    user.send_message('Please send nick name.', reply_markup=keyboards.en_back)
                    user.database.menu = 8
                elif text == 'Get Recent Messages':
                    functions.recent_message(user)
                elif text == 'Get User Recent Messages':
                    user.send_message('Please send user id.', reply_markup=keyboards.en_back)
                    user.database.menu = 9
                elif text == 'New Messages':
                    if (new_messages := models.Message.objects.filter(receiver=user.database, is_read=False)).exists():
                        user.send_message('New Messages 👇')
                        for new_message in new_messages:
                            user.send_message(
                                f'From : {new_message.sender.nick_name}\n'
                                f'Type : {new_message.message_type.replace("m", "Message").replace("r", "Reply")}\n'
                                f'Text : \n\n{new_message.text}',
                                keyboards.message(new_message.sender.token)
                            )
                        new_messages.update(is_read=True)
                    else:
                        user.send_message('شما هیچ پیام خوانده نشده ای ندراید ⚠️', reply_to_message_id=message_id)
                elif text == 'Get User':
                    user.send_message('Please send user id.', reply_markup=keyboards.en_back)
                    user.database.menu = 10
            elif user.database.menu == 2:
                if text == 'Back':
                    user.send_message(
                        'You are back to main menu .', reply_to_message_id=message_id, reply_markup=keyboards.admin
                    )
                    user.database.menu = 1
                else:
                    try:
                        user_id = int(text)
                    except (ValueError, TypeError):
                        user.send_message('User ID is not valid ⚠')
                    else:
                        user.database.menu = 1
                        functions.change_user_status(user_id, 'b')
                        user.send_message('User has been banned ☑', keyboards.admin)
            elif user.database.menu == 3:
                if text == 'Back':
                    user.send_message('Back to menu', reply_to_message_id=message_id, reply_markup=keyboards.admin)
                    user.database.menu = 1
                else:
                    try:
                        user_id = int(text)
                    except ValueError:
                        user.send_message('User ID is not valid ⚠')
                    else:
                        user.database.menu = 1
                        functions.change_user_status(user_id, 'a')
                        user.send_message('User has been unbanned ☑', keyboards.admin)
            elif user.database.menu == 4:
                if text == 'Back🔙':
                    user.send_message('You are back at the main menu .', reply_markup=keyboards.admin)
                    user.database.menu = 1
                else:
                    user_receiver = classes.User(token=user.database.token_last_receiver)
                    models.Message.objects.create(
                        message_id=message_id,
                        text=text,
                        sender=user.database,
                        receiver=user_receiver.database,
                        message_type='m'
                    )
                    user_receiver.send_message(f'شما یک پیام جدید از طرف {user.database.nick_name} دریافت کردید !')
                    user.send_message('Your message has been sent ✅', keyboards.admin)
                    user.database.menu = 1
            elif user.database.menu == 5:
                if text == 'بازگشت 🔙':
                    user.send_message('You are back at main menu .🔙', reply_markup=keyboards.admin)
                    user.database.menu = 1
                else:
                    user_receiver = classes.User(token=user.database.token_last_receiver)
                    models.Message.objects.create(
                        message_id=message_id,
                        text=text,
                        sender=user.database,
                        receiver=user_receiver.database,
                        message_type='r'
                    )
                    user_receiver.send_message(f'شما یک پاسخ جدید از طرف {user.database.nick_name} دریافت کردید !')
                    user.send_message('Message has been replied !', keyboards.admin)
                    user.database.menu = 1
            elif user.database.menu == 8:
                if user.database.last_menu == 1:
                    user.database.menu = 1
                    if text == 'Back':
                        user.send_message('You are back at the main menu !', keyboards.admin)
                    else:
                        user.database.nick_name = text
                        user.send_message('Nickname has been changed !', keyboards.admin)
                elif user.database.last_menu == 4:
                    user.database.last_menu = 4
                    user.send_message('Now you can send your message .', keyboards.en_back)
                else:
                    user.database.menu = 1
                    user.send_message('Welcome to Anonymous message bot !', keyboards.admin)
            elif user.database.menu == 9:
                if text == 'Back':
                    user.send_message('Back to menu', reply_to_message_id=message_id, reply_markup=keyboards.admin)
                    user.database.menu = 1
                else:
                    try:
                        user_id = int(text)
                    except (ValueError, TypeError):
                        user.send_message('User ID is not valid ⚠')
                    else:
                        functions.recent_message(user, chat_id=user_id)
                        user.send_message('Here are recent messages ☝️', keyboards.admin)
                        user.database.menu = 1
            elif user.database.menu == 10:
                if text == 'Back':
                    user.send_message('Back to menu', reply_to_message_id=message_id, reply_markup=keyboards.admin)
                    user.database.menu = 1
                else:
                    try:
                        user_id = int(text)
                    except (ValueError, TypeError):
                        user.send_message('User ID is not valid ⚠')
                    else:
                        user.send_message(
                            f'[{user_id}](tg://user?id={user_id})', reply_markup=keyboards.admin, parse_mode='Markdown'
                        )
                        user.database.menu = 1
        else:  # User Section
            if text.startswith('/'):  # Command Check
                text = text[1:]
                if (text := text.split())[0] == 'start':
                    if len(text) < 2:
                        if not user.database.nick_name:
                            user.send_message('یک نام برای خود تعیین کنید. ✏️\nاین نام برای دیگران قابل نمایش است. 🙊')
                            user.database.menu = 4
                            user.database.last_menu = 0
                        else:
                            user.send_message('به ربات پیام ناشناس خوش آمدید.', reply_markup=keyboards.user)
                            user.database.menu = 1
                    else:
                        try:
                            user_black_list = classes.User(token=text[1]).database.black_list.all()
                        except (ValidationError, models.User.DoesNotExist):
                            pass
                        else:
                            if user.database.nick_name:
                                if user.database in user_black_list:
                                    user.send_message(
                                        'شما در لیست سیاه کاربر مورد نظر میباشید. 💀', reply_markup=keyboards.user
                                    )
                                    user.database.menu = 1
                                else:
                                    user.database.token_last_receiver = text[1]
                                    user.send_message('پیام خود را ارسال کنید. ✍️', reply_markup=keyboards.fa_back)
                                    user.database.menu = 3
                            else:
                                user.send_message(
                                    'یک نام برای خود تعیین کنید. ✏️\nاین نام برای دیگران قابل نمایش است. 🙊'
                                )
                                user.database.menu = 4
                                user.database.last_menu = 3
                                user.database.token_last_receiver = text[1]
            elif user.database.menu == 1:
                if text == 'لینک  🔗':
                    user.send_url()
                elif text == 'ارتباط با مدیریت 📬':
                    user.send_message('برای تماس با مدیریت از بات زیر استفاده کنید.', reply_markup=keyboards.support_())
                elif text == 'حمایت ❤️':
                    user.send_message('مبلغ مورد نظر خود را وارد کنید.(تومان) 🙏', reply_markup=keyboards.fa_back)
                    user.database.menu = 2
                elif text == 'راهنما 🔰':
                    user.send_message(
                        'فقط کافیه لینک خودتون و بسازید تا با استفاده از اون لینک بتونید پیام هارو دریافت کنید.'
                    )
                elif text == 'تغییر نام ✍️':
                    user.send_message(
                        'یک نام برای خود تعیین کنید. ✏️\nاین نام برای دیگران قابل نمایش است. 🙊',
                        reply_markup=keyboards.fa_back
                    )
                    user.database.menu = 4
                    user.database.last_menu = 1
                elif text == 'لیست سیاه ☠️':
                    if user.database.black_list.exists():
                        user.send_message(
                            'لیست سیاه ‼️\n\nبرای خارج کردن از لسیت سیاه انتخاب کنید.',
                            reply_markup=keyboards.unblock(
                                [(
                                    user_kicked.nick_name, user_kicked.token
                                ) for user_kicked in user.database.black_list.all()]
                            )
                        )
                    else:
                        user.send_message('لیست سیاه شما خالی میباشید ⚠️', reply_to_message_id=message_id)
                elif text == 'پیام های اخیر 🗳':
                    functions.recent_message_user(user)
                elif text == 'پیام های جدید':
                    # Checking for channel
                    if not (
                            result := functions.get_chat_member('@SholexTeam', user.database.chat_id)
                    ) or result['status'] not in ('administrator', 'creator', 'member'):
                        user.send_message(
                            'برای استفاده از ربات باید در کانال زیر عضو شوید.️❤️❤️',
                            reply_markup=keyboards.sholex()
                        )
                        user.database.save()
                        return HttpResponse(status=200)
                    if (new_messages := models.Message.objects.filter(receiver=user.database, is_read=False)).exists():
                        user.send_message('پیام های جدید 👇')
                        for new_message in new_messages:
                            user.send_message(
                                f'از طرف : {new_message.sender.nick_name}\n'
                                f'نوع : {new_message.message_type.replace("m", "پیام").replace("r", "پاسخ")}\n'
                                f'متن : \n\n{new_message.text}',
                                keyboards.message(new_message.sender.token)
                            )
                        new_messages.update(is_read=True)
                    else:
                        user.send_message('شما هیچ پیام خوانده نشده ای ندارید ⚠️', reply_to_message_id=message_id)
            elif user.database.menu == 2:
                if text == 'بازگشت 🔙':
                    user.send_message('شما به منوی اصلی بازگشتید 🔙', reply_markup=keyboards.user)
                    user.database.menu = 1
                else:
                    try:
                        donate_money = int(text)
                    except (ValueError, TypeError):
                        user.send_message('مبلغ وارد شده معتبر نیست ✖️')
                    else:
                        user.database.menu = 1
                        user.send_message(
                            'برای حمایت مالی از دکمه ی زیر استفاده کنید ❤️',
                            keyboards.donate(donate_money * 10)
                        )
                        user.send_message('شما به منوی اصلی بازگشتید 🔙', keyboards.user)
            elif user.database.menu == 3:
                if text == 'بازگشت 🔙':
                    user.send_message('شما به منوی اصلی بازگشتید 🔙', reply_markup=keyboards.user)
                    user.database.menu = 1
                elif text != 'None':
                    user_receiver = classes.User(token=user.database.token_last_receiver)
                    models.Message.objects.create(
                        message_id=message_id,
                        text=text,
                        sender=user.database,
                        receiver=user_receiver.database,
                        message_type='m'
                    )
                    user_receiver.send_message(f'شما یک پیام جدید از طرف {user.database.nick_name} دریافت کردید !')
                    user.send_message('پیام شما ارسال شد ✅', keyboards.user)
                    user.database.menu = 1
                else:
                    user.send_message('شما فقط مجاز به ارسال متن هستید ❌')
            elif user.database.menu == 4:
                if user.database.last_menu == 1:
                    user.database.menu = 1
                    if text == 'بازگشت 🔙':
                        user.send_message('شما به منوی اصلی بازگشتید 🔙', keyboards.user)
                    else:
                        user.database.nick_name = text
                        user.send_message('نام کاربری شما تنظیم شد ☑️🔙', keyboards.user)
                elif user.database.last_menu == 3:
                    user.send_message('اکنون پیام خود را ارسال کنید ✔️', keyboards.fa_back)
                    user.database.nick_name = text
                    user.database.menu = 3
                else:
                    user.send_message('به ربات پیام نشاناس خوش آمدید !', keyboards.user)
                    user.database.menu = 1
                    user.database.nick_name = text
            elif user.database.menu == 5:
                if text == 'بازگشت 🔙':
                    user.send_message('شما به منوی اصلی بازگشتید 🔙', keyboards.user)
                    user.database.menu = 1
                elif text != 'None':
                    user_receiver = classes.User(token=user.database.token_last_receiver)
                    models.Message.objects.create(
                        message_id=message_id,
                        text=text,
                        sender=user.database,
                        receiver=user_receiver.database,
                        message_type='r'
                    )
                    user_receiver.send_message(f'شما یک پاسخ جدید از طرف {user.database.nick_name} دریافت کردید !')
                    user.send_message('پیام شما ارسال شد ✅', keyboards.user)
                    user.database.menu = 1
                else:
                    user.send_message('شما فقط قادر به ارسال متن هستید ❌')
        user.database.save()
        return HttpResponse(status=200)
