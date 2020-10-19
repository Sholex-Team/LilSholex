from persianmeme import functions, classes, keyboards, models, tasks
from LilSholex.functions import (
    save_obj, delete_obj, get_obj, create_obj, filter_by_ordering, get_by_ordering, exists_obj
)
from django.http import HttpResponse
import json
from . import translations


def webhook(request):
    update = json.loads(request.body.decode())
    answer_query = functions.answer_callback_query()
    if 'inline_query' in update:
        query = update['inline_query']['query']
        offset = update['inline_query']['offset']
        inline_query_id = update['inline_query']['id']
        user = classes.User(update['inline_query']['from']['id'])
        user.record_audio()
        if not user.database.started:
            user.save()
            functions.answer_inline_query(inline_query_id, functions.start_bot_first(), '', 0)
            return HttpResponse(status=200)
        user.send_ad()
        user.set_username()
        user.save()
        if user.database.status != 'f':
            results, next_offset = user.get_voices(query, offset)
            functions.answer_inline_query(inline_query_id, json.dumps(results), next_offset, 300)
    elif 'callback_query' in update:
        callback_query = update['callback_query']
        admin = classes.User(callback_query['from']['id'])
        query_id = callback_query['id']
        callback_data = callback_query['data'].split(':')
        try:
            message = callback_query['message']
        except KeyError:
            message = None
            message_id = None
        else:
            message_id = message['message_id']
        if callback_data[0] == 'read':
            user = classes.User(callback_data[1])
            user.database.sent_message = False
            user.send_message('پیام شما توسط مدیریت بررسی شد ✔')
            admin.delete_message(message_id)
            answer_query(query_id, 'Read ✅', False)
            user.save()
        elif callback_data[0] == 'ban':
            user = classes.User(callback_data[1])
            user.database.sent_message = False
            user.database.status = 'b'
            user.send_message('شما از استفاده از ربات محروم شدید 🚫')
            admin.delete_message(message_id)
            answer_query(query_id, f'User {user.database.chat_id} has been banned !', True)
            user.save()
        elif callback_data[0] == 'reply':
            user = classes.User(callback_data[1])
            admin.database.menu = 9
            admin.database.back_menu = 'chat_id'
            admin.database.temp_user_id = user.database.chat_id
            admin.send_message('Please send the text which you want to be replied !', keyboards.en_back)
            admin.delete_message(message_id)
            answer_query(query_id, 'Replying 🔴', False)
            user.database.sent_message = False
            user.send_message('پیام ارسالی شما توسط مدیریت بررسی شد ✅')
            user.save()
            admin.save()
        elif callback_data[0] in ('delete', 'delete_deny'):
            target_delete = functions.get_delete(callback_data[1])
            if not target_delete:
                return HttpResponse(status=200)
            user = classes.User(instance=target_delete.user)
            if callback_data[0] == 'delete':
                functions.delete_target_voice(target_delete)
                answer_query(query_id, 'Voice has been Deleted ✅', True)
                user.send_message('ویس درخواستی شما از ربات حذف شد ✅')
            elif callback_data[0] == 'delete_deny':
                delete_obj(target_delete)
                answer_query(query_id, 'Delete Request has been denied ☑', True)
                user.send_message('درخواست حذف ویس شما توسط مدیریت رد شد ❌')
            admin.delete_message(message_id)
        elif admin.database.rank != 'u' and callback_data[0] in ('accept', 'deny') and message.get('voice'):
            target_voice = functions.check_voice(message['voice']['file_unique_id'])
            if target_voice:
                if callback_data[0] == 'accept':
                    if not admin.like_voice(target_voice):
                        answer_query(query_id, 'You have voted this voice before !', True)
                    else:
                        answer_query(query_id, 'Voice has been voted ✅', False)
                else:
                    if not admin.dislike_voice(target_voice):
                        answer_query(query_id, 'You have voted this voice before ⚠️', True)
                    else:
                        answer_query(query_id, 'Voice has been denied ✖️', False)
                save_obj(target_voice)
                target_voice.edit_vote_count(message_id)
        else:
            user = classes.User(callback_query['from']['id'])
            user.record_audio()
            if user.database.started:
                user.send_ad()
            if callback_data[0] == 'up':
                try:
                    voice = get_obj(models.Voice, voice_id=callback_data[1])
                except models.Voice.DoesNotExist:
                    pass
                else:
                    if user.database in voice.voters.all():
                        answer_query(query_id, 'شما قبلا به این ویس رای داده اید ❌', False)
                    else:
                        user.add_voter(voice)
                        voice.votes += 1
                        save_obj(voice)
                        answer_query(query_id, 'شما به این ویس رای 👍 دادید !', False)
            elif callback_data[0] == 'down':
                try:
                    voice = get_obj(models.Voice, voice_id=callback_data[1])
                except models.Voice.DoesNotExist:
                    pass
                else:
                    if user.database in voice.voters.all():
                        user.remove_voter(voice)
                        voice.votes -= 1
                        save_obj(voice)
                        answer_query(query_id, 'شما رای خود را پس گرفتید ✔', False)
                    else:
                        answer_query(query_id, 'شما هنوز رای نداده اید ✖', False)
            user.save()
    else:
        if 'message' in update:
            message = update['message']
        elif 'edited_message' in update:
            message = update['edited_message']
        else:
            return HttpResponse(status=200)
        text = message.get('text', None)
        message_id = message['message_id']
        user = classes.User(message['chat']['id'])
        user.set_username()
        if text in ('بازگشت 🔙', 'Back 🔙'):
            user.go_back()
            return HttpResponse(status=200)
        if user.database.rank != 'u':
            if text == '/start':
                user.database.menu = 1
                user.send_message('Welcome to Admin Panel !', keyboards.owner, message_id)
            elif user.database.menu == 1:
                user.database.back_menu = 'main'
                # All Admins Section
                if text == 'Add Sound':
                    user.database.menu = 2
                    user.send_message(translations.admin_messages['voice_name'], keyboards.en_back)
                elif text == 'Voice Count':
                    user.send_message(functions.count_voices())
                elif text == 'Member Count':
                    user.send_message(f'All members count : {functions.count_users()}')
                # Admins & Owner section
                elif user.database.rank in ('a', 'o') and text in (
                        'Get User', 'Ban a User', 'Unban a User', 'Full Ban', 'Delete Sound'
                ):
                    if text == 'Get User':
                        user.database.menu = 12
                        user.send_message('Please send the user_id .', keyboards.en_back)
                    elif text == 'Ban a User':
                        user.database.menu = 5
                        user.send_message('Please send user id .', keyboards.en_back)
                    elif text == 'Unban a User':
                        user.database.menu = 6
                        user.send_message('Please send user id to unban !', keyboards.en_back)
                    elif text == 'Full Ban':
                        user.database.menu = 7
                        user.send_message(
                            'Please send the user id which you want it to be full banned !', keyboards.en_back
                        )
                    elif text == 'Delete Sound':
                        user.database.menu = 4
                        user.send_message(
                            'Please send the voice file which you want to delete !', keyboards.en_back
                        )
                # Owner Section
                elif user.database.rank == 'o' and text in (
                        'Message User', 'Add Ad', 'Delete Ad', 'Delete Requests', 'Broadcast'
                ):
                    if text == 'Message User':
                        user.database.menu = 8
                        user.send_message(translations.admin_messages['chat_id'], keyboards.en_back)
                    elif text == 'Add Ad':
                        user.database.menu = 10
                        user.send_message('Please send the Update Information .', keyboards.en_back)
                    elif text == 'Delete Ad':
                        user.database.menu = 11
                        user.send_message('Please send the Ad ID .', keyboards.en_back)
                    elif text == 'Delete Requests':
                        delete_requests = functions.get_delete_requests()
                        if delete_requests:
                            for delete_request in delete_requests:
                                user.send_voice(
                                    delete_request.get_voice().file_id,
                                    f'From : {delete_request.get_user().chat_id}',
                                    keyboards.delete_voice(delete_request.delete_id)
                                )
                            user.send_message('Here are delete requests 👆', reply_to_message_id=message_id)
                        else:
                            user.send_message(
                                'There is no more delete requests !', reply_to_message_id=message_id
                            )
                    elif text == 'Broadcast':
                        user.database.menu = 13
                        user.send_message('Please sent the message you want to broadcast .', keyboards.en_back)
                elif 'voice' in message:
                    search_result = functions.get_voice(message['voice']['file_unique_id'])
                    if search_result:
                        target_voice_name = search_result.name
                        user.send_message(
                            f'Voice Name : {target_voice_name}\n\nYou can use it by typing\n\n'
                            f'@Persian_Meme_Bot {target_voice_name}\n\nin a chat 😁',
                            keyboards.use(target_voice_name)
                        )
                    else:
                        user.send_message('I could not find this voice ☹')
                else:
                    user.send_message('Unknown Command ⚠')
            elif user.database.menu == 2:
                if text:
                    if len(text) > 50:
                        user.send_message('Voice name is longer than limit !')
                    else:
                        user.database.menu = 3
                        user.database.temp_voice_name = text
                        user.database.back_menu = 'voice_name'
                        user.send_message('Now send the voice file .')
                else:
                    user.send_message('Please send a name !')
            elif user.database.menu == 3:
                if 'voice' in message:
                    if functions.add_voice(
                            message['voice']['file_id'],
                            message['voice']['file_unique_id'],
                            user.database.temp_voice_name,
                            user.database,
                            'a'
                    ):
                        user.database.menu = 1
                        user.send_message('Voice has been added to database ✅', keyboards.owner)
                    else:
                        user.send_message('Voice is already in the database ❌')
                else:
                    user.send_message('Please send a valid voice file !')
            elif user.database.menu == 4:
                if 'voice' in message:
                    user.delete_voice(message['voice']['file_unique_id'])
                    user.database.menu = 1
                    user.send_message('Voice has been deleted 🗑', keyboards.owner)
                else:
                    user.send_message('Voice File is not Valid !')
            elif user.database.menu == 5:
                try:
                    user_id = int(text)
                except (ValueError, TypeError):
                    user.send_message('User ID is not valid ⚠')
                else:
                    user.database.menu = 1
                    functions.change_user_status(user_id, 'b')
                    user.send_message('User has been banned ❌', keyboards.owner)
            elif user.database.menu == 6:
                try:
                    user_id = int(text)
                except (ValueError, TypeError):
                    user.send_message('User ID is not valid ⚠')
                else:
                    user.database.menu = 1
                    functions.change_user_status(user_id, 'a')
                    user.send_message('User has been unbanned ☑', keyboards.owner)
            elif user.database.menu == 7:
                try:
                    user_id = int(text)
                except (ValueError, TypeError):
                    user.send_message('User ID is not valid ⚠')
                else:
                    user.database.menu = 1
                    functions.change_user_status(user_id, 'f')
                    user.send_message('User has been Full Banned !', keyboards.owner)
            elif user.database.menu == 8:
                try:
                    user.database.temp_user_id = int(text)
                except (ValueError, TypeError):
                    user.send_message('You must use a number as User ID !')
                else:
                    user.database.menu = 9
                    user.database.back_menu = 'chat_id'
                    user.send_message('Now send the text which you want to be delivered .')
            elif user.database.menu == 9:
                user.database.menu = 1
                classes.User(user.database.temp_user_id).send_message(f'پیام از طرف مدیریت 👇\n\n{text}')
                user.send_message('Message has been sent to user ✔', keyboards.owner)
            elif user.database.menu == 10:
                user.database.menu = 1
                ad_id = create_obj(models.Ad, chat_id=user.database.chat_id, message_id=message_id).ad_id
                user.send_message(
                    f'Update message has been submitted ✔️\nAd ID : {ad_id}', keyboards.owner
                )
            elif user.database.menu == 11:
                try:
                    models.Ad.objects.get(ad_id=int(text)).delete()
                except (ValueError, models.Ad.DoesNotExist):
                    user.send_message('Ad ID not found !', reply_to_message_id=message_id)
                else:
                    user.database.menu = 1
                    user.send_message('Ad has been deleted ❌', keyboards.owner)
            elif user.database.menu == 12:
                try:
                    int(text)
                except ValueError:
                    user.send_message('User ID must be a number !', reply_to_message_id=message_id)
                else:
                    user.database.menu = 1
                    user.send_message(
                        f'Here is user profile 👇\n\n[{text}](tg://user?id={text})',
                        keyboards.owner,
                        message_id,
                        'Markdown'
                    )
            elif user.database.menu == 13:
                user.broadcast(message_id)
        elif user.database.status == 'a' and user.database.rank == 'u':
            user.send_ad()
            if text == '/start':
                user.database.menu = 1
                user.send_message('به ربات Persian Meme خوش آمدید 😁', keyboards.user, message_id)
            elif user.database.menu == 1:
                user.database.back_menu = 'main'
                if text == 'راهنما 🔰':
                    user.send_help()
                elif text == 'آخرین ویس ها 🆕':
                    voices_str = ''
                    for voice in filter_by_ordering(models.Voice, '-voice_id', status='a', voice_type='n')[:15]:
                        voices_str += f'⭕ {voice.name}\n'
                    user.send_message(voices_str)
                elif text == 'ارتباط با مدیریت 📬':
                    if user.database.sent_message:
                        user.send_message('پیام قبلی شما در انتظار مشاهده است ⚠')
                    else:
                        user.database.menu = 2
                        user.send_message('لطفا پیام خود را در قالب متن ارسال کنید !', keyboards.per_back)
                elif text == 'پیشنهاد ویس 🔥':
                    if models.Voice.objects.filter(sender=user.database, status=models.Voice.Status.pending).exists():
                        user.send_message('ویس قبلی شما در انتظار تایید است ❌')
                    else:
                        user.database.menu = 3
                        user.send_message(translations.user_messages['voice_name'], keyboards.per_back)
                elif text == 'حذف ویس ❌':
                    user.database.menu = 5
                    user.send_message(
                        'لطفا یکی از ویس های پیشنهادی خود را جهت حذف ارسال کنید', keyboards.per_back
                    )
                elif text == 'ویس های محبوب 👌':
                    voices_str = ''
                    for voice in get_by_ordering(models.Voice, '-votes')[:15]:
                        voices_str += f'⭕ {voice.name}\n'
                    user.send_message(voices_str)
                elif text == 'امتیازدهی ⭐':
                    user.database.menu = 6
                    user.send_message('لطفا یکی از گزینه های زیر را انتخاب کنید .', keyboards.toggle)
                elif text == 'مرتب سازی 🗂':
                    user.database.menu = 7
                    user.send_message('لطفا یکی از روش های مرتب سازی زیر را انتخاب کنید 👇', keyboards.voice_order)
                elif text == 'درخواست حذف ویس ✖':
                    if exists_obj(user.database.deletes_user):
                        user.send_message('درخواست قبلی شما در حال بررسی است ⚠')
                    else:
                        user.database.menu = 8
                        user.send_message('لطفا ویس مورد نظر را ارسال کنید .', keyboards.per_back)
                elif text == 'ویس های شخصی 🔒':
                    user.database.menu = 11
                    user.send_message(translations.user_messages['choices'], keyboards.private)
                elif text == 'علاقه مندی ها ❤️':
                    user.database.menu = 15
                    user.send_message(translations.user_messages['choices'], keyboards.private)
                elif 'voice' in message:
                    search_result = functions.get_voice(message['voice']['file_unique_id'])
                    if search_result:
                        target_voice_name = search_result.name
                        user.send_message(
                            f'نام ویس : {target_voice_name}\n\nشما میتوانید با تایپ\n\n'
                            f'@Persian_Meme_Bot {target_voice_name}\n\n از این ویس استفاده کنید 😁',
                            keyboards.use(target_voice_name)
                        )
                    else:
                        user.send_message('نتونستم این ویس رو پیدا کنم ☹')
                else:
                    user.send_message('دستور ناشناخته ⚠')
            elif user.database.menu == 2:
                user.database.menu = 1
                owner = classes.User(instance=functions.get_owner())
                owner.send_message(
                    f'New Message from {user.database.chat_id} 👇\n\n {text}',
                    keyboards.message(user.database.chat_id)
                )
                user.database.sent_message = True
                user.send_message('پیام شما به مدیریت ارسال شد ✔', keyboards.user, message_id)
            elif user.database.menu == 3:
                if text:
                    if len(text) > 50:
                        user.send_message('نام ویس بیش از حد طولانی است ❌')
                    else:
                        user.database.menu = 4
                        user.database.temp_voice_name = text
                        user.database.back_menu = 'suggest_name'
                        user.send_message('لطفا ویس مورد نظر را ارسال کنید .')
                else:
                    user.send_message('لطفا یک متن به عنوان اسم ویس وارد کنید ⚠')
            elif user.database.menu == 4:
                if 'voice' in message:
                    target_voice = functions.add_voice(
                        message['voice']['file_id'],
                        message['voice']['file_unique_id'],
                        user.database.temp_voice_name,
                        user.database,
                        'p'
                    )
                    if target_voice:
                        user.database.menu = 1
                        target_voice.message_id = target_voice.send_voice()
                        tasks.check_voice(target_voice.voice_id)
                        user.send_message(
                            'ویس پیشنهادی شما برای تایید به مدیریت ارسال شد ✅', keyboards.user
                        )
                        save_obj(target_voice)
                    else:
                        user.send_message('این ویس در ربات موجود میباشد ⚠', reply_to_message_id=message_id)
                else:
                    user.send_message('لطفا یک ویس ارسال کنید ⚠')
            elif user.database.menu == 5:
                if 'voice' in message:
                    if user.remove_voice(message['voice']['file_unique_id']):
                        user.database.menu = 1
                        user.send_message('ویس شما با موفقیت حذف شد 🗑', keyboards.user)
                    else:
                        user.send_message('ویس ارسالی متعلق به شما نبوده و یا در ربات موجود نمیباشد ❌')
                else:
                    user.send_message('لطفا یک ویس ارسال کنید 🔴')
            elif user.database.menu == 6:
                if text == 'روشن 🔛':
                    user.database.vote = True
                    user.database.menu = 1
                    user.send_message('سیستم امتیازدهی برای شما روشن شد 🔛', keyboards.user)
                elif text == 'خاموش 🔴':
                    user.database.vote = False
                    user.database.menu = 1
                    user.send_message('سیستم امتیازدهی برای شما خاموش شد 🔴', keyboards.user)
                else:
                    user.send_message('انتخاب نامعتبر ⚠')
            elif user.database.menu == 7:
                if text == 'جدید به قدیم':
                    user.database.voice_order = '-voice_id'
                    user.database.menu = 1
                    user.send_message('مرتب سازی ویس های تغییر کرد ✅', keyboards.user)
                elif text == 'قدیم به جدید':
                    user.database.voice_order = 'voice_id'
                    user.database.menu = 1
                    user.send_message('مرتب سازی ویس های تغییر کرد ✅', keyboards.user)
                elif text == 'بهترین به بدترین':
                    user.database.voice_order = '-votes'
                    user.database.menu = 1
                    user.send_message('مرتب سازی ویس های تغییر کرد ✅', keyboards.user)
                elif text == 'بدترین به بهترین':
                    user.database.voice_order = 'votes'
                    user.database.menu = 1
                    user.send_message('مرتب سازی ویس های تغییر کرد ✅', keyboards.user)
                else:
                    user.send_message('دستور نامعتبر ⚠')
            elif user.database.menu == 8:
                if 'voice' in message:
                    target_voice = functions.get_voice(
                        message['voice']['file_unique_id']
                    )
                    if target_voice:
                        owner = classes.User(instance=functions.get_owner())
                        user.database.menu = 1
                        user.send_message('درخواست شما با موفقیت ثبت شد ✅', keyboards.user, message_id)
                        user.delete_request(target_voice)
                        owner.send_message('New delete request 🗑')
                    else:
                        user.send_message('ویس ارسالی یافت نشد !')
                else:
                    user.send_message('لطفا یک ویس ارسال کنید ⚠')
            elif user.database.menu == 11:
                if text == 'افزودن ⏬':
                    if user.private_user_count() <= 60:
                        user.database.menu = 12
                        user.database.back_menu = 'private'
                        user.send_message(translations.user_messages['voice_name'], keyboards.per_back)
                    else:
                        user.send_message('شما حداکثر تعداد ویس های شخصی را ارسال کرده اید ⚠️')
                elif text == 'حذف 🗑':
                    user.database.menu = 13
                    user.database.back_menu = 'private'
                    user.send_message('ویس مورد نظر را ارسال کنید .', keyboards.per_back)
                else:
                    user.send_message('دستور نامعتبر ⚠️')
            elif user.database.menu == 12:
                if text:
                    if len(text) > 50:
                        user.send_message('نام طولانی تر از حد مجاز است ❌')
                    else:
                        user.database.temp_voice_name = text
                        user.database.menu = 14
                        user.database.back_menu = 'private_name'
                        user.send_message('لطفا ویس را ارسال کنید .')
                else:
                    user.send_message('لطفا یک نام وارد کنید ⚠️')
            elif user.database.menu == 13:
                if 'voice' in message:
                    current_voice = functions.get_voice(
                        message['voice']['file_unique_id'], voice_type='p'
                    )
                    if current_voice:
                        if user.delete_private_voice(current_voice):
                            user.database.menu = 11
                            user.database.back_menu = 'main'
                            user.send_message('ویس مورد نظر از ربات حذف شد !', keyboards.private)
                        else:
                            user.send_message('ویس مورد نظر از ویس های شخصی شما نیست ❌')
                    else:
                        user.send_message('ویس ارسالی یافت نشد !')
                else:
                    user.send_message('ویس ارسالی معتبر نیست ❌')
            elif user.database.menu == 14:
                if 'voice' in message:
                    if not functions.get_voice(message['voice']['file_unique_id']):
                        user.create_private_voice(message)
                        user.database.menu = 11
                        user.database.back_menu = 'main'
                        user.send_message('این ویس به لیست ویس های شما اضافه شد ✅', keyboards.private)
                    else:
                        user.send_message('این ویس در ربات موجود است ❌')
                else:
                    user.send_message('لطفا یک ویس ارسال کنید ✖️')
            elif user.database.menu == 15:
                if text == 'افزودن ⏬':
                    if user.count_favorite_voices() <= 30:
                        user.database.menu = 16
                        user.database.back_menu = 'favorite'
                        user.send_message('لطفا ویس مورد نظر را ارسال کنید .', keyboards.per_back)
                    else:
                        user.send_message('شما حداکثر تعداد ویس های مورد علاقه را اضافه کرده اید ⚠️')
                elif text == 'حذف 🗑':
                    user.database.menu = 17
                    user.database.back_menu = 'favorite'
                    user.send_message('ویس مورد نظر را ارسال کنید .', keyboards.per_back)
                else:
                    user.send_message('دستور نامعتبر ⚠️')
            elif user.database.menu == 16:
                if 'voice' in message:
                    current_voice = functions.get_voice(message['voice']['file_unique_id'])
                    if current_voice:
                        if user.add_favorite_voice(current_voice):
                            user.database.menu = 15
                            user.database.back_menu = 'main'
                            user.send_message(
                                'ویس مورد نظر به لیست علاقه مندی های شما اضافه شد ✔️',
                                keyboards.private
                            )
                        else:
                            user.send_message('ویس در لیست موجود است ❌')
                    else:
                        user.send_message('این ویس در ربات موجود نیست ❌')
                else:
                    user.send_message('لطفا یک ویس ارسال کنید !')
            elif user.database.menu == 17:
                if 'voice' in message:
                    current_voice = functions.get_voice(message['voice']['file_unique_id'])
                    if current_voice:
                        user.delete_favorite_voice(current_voice)
                        user.database.menu = 15
                        user.database.back_menu = 'main'
                        user.send_message('ویس از لیست حذف شد !', keyboards.private)
                    else:
                        user.send_message('این ویس در ربات موجود نیست !')
                else:
                    user.send_message('لطفا یک ویس ارسال کنید !')
        user.save()
    return HttpResponse(status=200)
