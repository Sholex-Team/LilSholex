from persianmeme import functions, classes, keyboards, models, tasks
from LilSholex.functions import (
    save_obj, delete_obj, get_obj, create_obj, filter_by_ordering, get_by_ordering, exists_obj
)
from django.http import HttpResponse
import aiohttp
import json


async def webhook_view(request):
    update = json.loads(request.body.decode())
    answer_query = functions.answer_callback_query(request.http_session)
    if 'inline_query' in update:
        user = await classes.User(request.http_session, update['inline_query']['from']['id'])
        await user.send_ad()
        await user.set_username()
        await user.save()
        if user.database.status != 'f':
            query = update['inline_query']['query']
            offset = update['inline_query']['offset']
            inline_query_id = update['inline_query']['id']
            results, next_offset = await user.get_voices(query, offset)
            await functions.answer_inline_query(
                inline_query_id, json.dumps(results), next_offset, 300, request.http_session
            )
    elif 'callback_query' in update:
        callback_query = update['callback_query']
        admin = await classes.User(request.http_session, callback_query['from']['id'])
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
            user = await classes.User(request.http_session, callback_data[1])
            user.database.sent_message = False
            await user.send_message('پیام شما توسط مدیریت بررسی شد ✔')
            await admin.delete_message(message_id)
            await answer_query(query_id, 'Read ✅', False)
            await user.save()
        elif callback_data[0] == 'ban':
            user = await classes.User(request.http_session, callback_data[1])
            user.database.sent_message = False
            user.database.status = 'b'
            await user.send_message('شما از استفاده از ربات محروم شدید 🚫')
            await admin.delete_message(message_id)
            await answer_query(query_id, f'User {user.database.chat_id} has been banned !', True)
            await user.save()
        elif callback_data[0] == 'reply':
            user = await classes.User(request.http_session, callback_data[1])
            admin.database.menu = 9
            admin.database.temp_user_id = user.database.chat_id
            await admin.send_message('Please send the text which you want to be replied !', keyboards.en_back)
            await admin.delete_message(message_id)
            await answer_query(query_id, 'Replying 🔴', False)
            user.database.sent_message = False
            await user.send_message('پیام ارسالی شما توسط مدیریت بررسی شد ✅')
            await user.save()
            await admin.save()
        elif callback_data[0] in ('delete', 'delete_deny'):
            if not (target_delete := await functions.get_delete(callback_data[1])):
                return HttpResponse(status=200)
            user = await classes.User(request.http_session, instance=target_delete.user)
            if callback_data[0] == 'delete':
                await functions.delete_target_voice(target_delete)
                await answer_query(query_id, 'Voice has been Deleted ✅', True)
                await user.send_message('ویس درخواستی شما از ربات حذف شد ✅')
            elif callback_data[0] == 'delete_deny':
                await delete_obj(target_delete)
                await answer_query(query_id, 'Delete Request has been denied ☑', True)
                await user.send_message('درخواست حذف ویس شما توسط مدیریت رد شد ❌')
            await admin.delete_message(message_id)
        elif admin.database.rank != 'u' and callback_data[0] in ('accept', 'deny') and message.get('voice'):
            if target_voice := await functions.check_voice(message['voice']['file_unique_id']):
                if callback_data[0] == 'accept':
                    if not await admin.like_voice(target_voice):
                        await answer_query(query_id, 'You have voted this voice before !', True)
                    else:
                        await answer_query(query_id, 'Voice has been voted ✅', False)
                else:
                    if not await admin.dislike_voice(target_voice):
                        await answer_query(query_id, 'You have voted this voice before ⚠️', True)
                    else:
                        await answer_query(query_id, 'Voice has been denied ✖️', False)
                await save_obj(target_voice)
                await target_voice.edit_vote_count(message_id, request.http_session)
        else:
            user = await classes.User(request.http_session, callback_query['from']['id'])
            await user.send_ad()
            if callback_data[0] == 'up':
                try:
                    voice = await get_obj(models.Voice, voice_id=callback_data[1])
                except models.Voice.DoesNotExist:
                    pass
                else:
                    if user.database in await voice.get_voters():
                        await answer_query(query_id, 'شما قبلا به این ویس رای داده اید ❌', False)
                    else:
                        await user.add_voter(voice)
                        voice.votes += 1
                        await save_obj(voice)
                        await answer_query(query_id, 'شما به این ویس رای 👍 دادید !', False)
            elif callback_data[0] == 'down':
                try:
                    voice = await get_obj(models.Voice, voice_id=callback_data[1])
                except models.Voice.DoesNotExist:
                    pass
                else:
                    if user.database in await voice.get_voters():
                        await user.remove_voter(voice)
                        voice.votes -= 1
                        await save_obj(voice)
                        await answer_query(query_id, 'شما رای خود را پس گرفتید ✔', False)
                    else:
                        await answer_query(query_id, 'شما هنوز رای نداده اید ✖', False)
            await user.save()
    else:
        if 'message' in update:
            message = update['message']
        elif 'edited_message' in update:
            message = update['edited_message']
        else:
            return HttpResponse(status=200)
        text = message.get('text', None)
        message_id = message['message_id']
        user = await classes.User(request.http_session, message['chat']['id'])
        await user.set_username()
        if user.database.rank != 'u':
            if text == '/start':
                user.database.menu = 1
                await user.send_message('Welcome to Admin Panel !', keyboards.owner, message_id)
            elif user.database.menu == 1:
                # All Admins Section
                if text == 'Add Sound':
                    user.database.menu = 2
                    await user.send_message('Please send the voice name to add !', keyboards.en_back)
                elif text == 'Voice Count':
                    await user.send_message(await functions.count_voices())
                elif text == 'Member Count':
                    await user.send_message(f'All members count : {await functions.count_users()}')
                # Admins & Owner section
                elif user.database.rank in ('a', 'o') and text in (
                        'Get User', 'Ban a User', 'Unban a User', 'Full Ban', 'Delete Sound'
                ):
                    if text == 'Get User':
                        user.database.menu = 12
                        await user.send_message('Please send the user_id .', keyboards.en_back)
                    elif text == 'Ban a User':
                        user.database.menu = 5
                        await user.send_message('Please send user id .', keyboards.en_back)
                    elif text == 'Unban a User':
                        user.database.menu = 6
                        await user.send_message('Please send user id to unban !', keyboards.en_back)
                    elif text == 'Full Ban':
                        user.database.menu = 7
                        await user.send_message(
                            'Please send the user id which you want it to be full banned !', keyboards.en_back
                        )
                    elif text == 'Delete Sound':
                        user.database.menu = 4
                        await user.send_message(
                            'Please send the voice file which you want to delete !', keyboards.en_back
                        )
                # Owner Section
                elif user.database.rank == 'o' and text in (
                        'Message User', 'Add Ad', 'Delete Ad', 'Delete Requests'
                ):
                    if text == 'Message User':
                        user.database.menu = 8
                        await user.send_message('Please send Target User ID .', keyboards.en_back)
                    elif text == 'Add Ad':
                        user.database.menu = 10
                        await user.send_message('Please send the Update Information .', keyboards.en_back)
                    elif text == 'Delete Ad':
                        user.database.menu = 11
                        await user.send_message('Please send the Ad ID .', keyboards.en_back)
                    elif text == 'Delete Requests':
                        if delete_requests := await functions.get_delete_requests():
                            for delete_request in delete_requests:
                                await user.send_voice(
                                    (await delete_request.get_voice()).file_id,
                                    f'From : {(await delete_request.get_user()).chat_id}',
                                    keyboards.delete_voice(delete_request.delete_id)
                                )
                            await user.send_message('Here are delete requests 👆', reply_to_message_id=message_id)
                        else:
                            await user.send_message(
                                'There is no more delete requests !', reply_to_message_id=message_id
                            )
                elif 'voice' in message:
                    if search_result := await functions.get_voice(message['voice']['file_unique_id']):
                        target_voice_name = search_result.name
                        await user.send_message(
                            f'Voice Name : {target_voice_name}\n\nYou can use it by typing\n\n'
                            f'@Persian_Meme_Bot {target_voice_name}\n\nin a chat 😁',
                            keyboards.use(target_voice_name)
                        )
                    else:
                        await user.send_message('I could not find this voice ☹')
                else:
                    await user.send_message('Unknown Command ⚠')
            elif user.database.menu == 2:
                if text == 'Back 🔙':
                    user.database.menu = 1
                    await user.send_message('You are back at the main menu 🔙', keyboards.owner)
                else:
                    if text:
                        if len(text) > 50:
                            await user.send_message('Voice name is longer than limit !')
                        else:
                            user.database.menu = 3
                            user.database.temp_voice_name = text
                            await user.send_message('Now send the voice file .')
                    else:
                        await user.send_message('Please send a name !')
            elif user.database.menu == 3:
                if text == 'Back 🔙':
                    user.database.menu = 2
                    await user.send_message('Please send the Voice Name .')
                else:
                    if 'voice' in message:
                        if await functions.add_voice(
                                message['voice']['file_id'],
                                message['voice']['file_unique_id'],
                                user.database.temp_voice_name,
                                user.database,
                                'a'
                        ):
                            user.database.menu = 1
                            await user.send_message('Voice has been added to database ✅', keyboards.owner)
                        else:
                            await user.send_message('Voice is already in the database ❌')
                    else:
                        await user.send_message('Please send a valid voice file !')
            elif user.database.menu == 4:
                if text == 'Back 🔙':
                    user.database.menu = 1
                    await user.send_message('You are the main menu !', keyboards.owner)
                else:
                    if 'voice' in message:
                        await functions.delete_voice(message['voice']['file_unique_id'])
                        user.database.menu = 1
                        await user.send_message('Voice has been deleted 🗑', keyboards.owner)
                    else:
                        await user.send_message('Voice File is not Valid !')
            elif user.database.menu == 5:
                if text == 'Back 🔙':
                    user.database.menu = 1
                    await user.send_message('You are back at the main menu 🔙', keyboards.owner)
                else:
                    try:
                        user_id = int(text)
                    except (ValueError, TypeError):
                        await user.send_message('User ID is not valid ⚠')
                    else:
                        user.database.menu = 1
                        await functions.change_user_status(user_id, 'b')
                        await user.send_message('User has been banned ❌', keyboards.owner)
            elif user.database.menu == 6:
                if text == 'Back 🔙':
                    user.database.menu = 1
                    await user.send_message('You are back at the main menu 🔙', keyboards.owner)
                else:
                    try:
                        user_id = int(text)
                    except (ValueError, TypeError):
                        await user.send_message('User ID is not valid ⚠')
                    else:
                        user.database.menu = 1
                        await functions.change_user_status(user_id, 'a')
                        await user.send_message('User has been unbanned ☑', keyboards.owner)
            elif user.database.menu == 7:
                if text == 'Back 🔙':
                    user.database.menu = 1
                    await user.send_message('You are back at the main menu 🔙', keyboards.owner)
                else:
                    try:
                        user_id = int(text)
                    except (ValueError, TypeError):
                        await user.send_message('User ID is not valid ⚠')
                    else:
                        user.database.menu = 1
                        await functions.change_user_status(user_id, 'f')
                        await user.send_message('User has been Full Banned !', keyboards.owner)
            elif user.database.menu == 8:
                if text == 'Back 🔙':
                    user.database.menu = 1
                    await user.send_message('You are back at the main menu !', keyboards.owner)
                else:
                    try:
                        user.database.temp_user_id = int(text)
                    except (ValueError, TypeError):
                        await user.send_message('You must use a number as User ID !')
                    else:
                        user.database.menu = 9
                        await user.send_message('Now send the text which you want to be delivered .')
            elif user.database.menu == 9:
                if text == 'Back 🔙':
                    user.database.menu = 8
                    await user.send_message('Please send the user Chat ID .')
                else:
                    user.database.menu = 1
                    await (
                        await classes.User(request.http_session, user.database.temp_user_id)
                    ).send_message(f'پیام از طرف مدیریت 👇\n\n{text}')
                    await user.send_message('Message has been sent to user ✔', keyboards.owner)
            elif user.database.menu == 10:
                user.database.menu = 1
                if text == 'Back 🔙':
                    await user.send_message('You are back at the main menu 🔙', keyboards.owner)
                else:
                    ad_id = (await create_obj(models.Ad, chat_id=user.database.chat_id, message_id=message_id)).ad_id
                    await user.send_message(
                        f'Update message has been submitted ✔️\nAd ID : {ad_id}', keyboards.owner
                    )
            elif user.database.menu == 11:
                if text == 'Back 🔙':
                    user.database.menu = 1
                    await user.send_message('You are back at the main menu 🔙', keyboards.owner)
                else:
                    try:
                        delete_obj(get_obj(models.Ad, ad_id=int(text)))
                    except (ValueError, models.Ad.DoesNotExist):
                        await user.send_message('Ad ID not found !', reply_to_message_id=message_id)
                    else:
                        user.database.menu = 1
                        await user.send_message('Ad has been deleted ❌', keyboards.owner)
            elif user.database.menu == 12:
                if text == 'Back 🔙':
                    user.database.menu = 1
                    await user.send_message('You are back at main menu 🔙', keyboards.owner, message_id)
                else:
                    try:
                        int(text)
                    except ValueError:
                        await user.send_message('User ID must be a number !', reply_to_message_id=message_id)
                    else:
                        user.database.menu = 1
                        await user.send_message(
                            f'Here is user profile 👇\n\n[{text}](tg://user?id={text})',
                            keyboards.owner,
                            message_id,
                            'Markdown'
                        )
        elif user.database.status == 'a' and user.database.rank == 'u':
            await user.send_ad()
            if text == '/start':
                user.database.menu = 1
                await user.send_message('به ربات Persian Meme خوش آمدید 😁', keyboards.user, message_id)
            elif user.database.menu == 1:
                if text == 'راهنما 🔰':
                    await user.send_message('برای استفاده از ربات کافیست آیدی ربات @Persian_Meme_Bot را در چت تایپ '
                                            'کنید !')
                elif text == 'آخرین ویس ها 🆕':
                    voices_str = ''
                    for voice in (await filter_by_ordering(models.Voice, '-voice_id', status='a', voice_type='n'))[:15]:
                        voices_str += f'⭕ {voice.name}\n'
                    await user.send_message(voices_str)
                elif text == 'ارتباط با مدیریت 📬':
                    if user.database.sent_message:
                        await user.send_message('پیام قبلی شما در انتظار مشاهده است ⚠')
                    else:
                        user.database.menu = 2
                        await user.send_message('لطفا پیام خود را در قالب متن ارسال کنید !', keyboards.per_back)
                elif text == 'پیشنهاد ویس 🔥':
                    if user.database.sent_voice:
                        await user.send_message('ویس قبلی شما در انتظار تایید است ❌')
                    else:
                        user.database.menu = 3
                        await user.send_message('لطفا نام ویس پیشنهادی را ارسال کنید .', keyboards.per_back)
                elif text == 'حذف ویس ❌':
                    user.database.menu = 5
                    await user.send_message(
                        'لطفا یکی از ویس های پیشنهادی خود را جهت حذف ارسال کنید', keyboards.per_back
                    )
                elif text == 'ویس های محبوب 👌':
                    voices_str = ''
                    for voice in (await get_by_ordering(models.Voice, '-votes'))[:15]:
                        voices_str += f'⭕ {voice.name}\n'
                    await user.send_message(voices_str)
                elif text == 'امتیازدهی ⭐':
                    user.database.menu = 6
                    await user.send_message('لطفا یکی از گزینه های زیر را انتخاب کنید .', keyboards.toggle)
                elif text == 'مرتب سازی 🗂':
                    user.database.menu = 7
                    await user.send_message('لطفا یکی از روش های مرتب سازی زیر را انتخاب کنید 👇',
                                            keyboards.voice_order)
                elif text == 'درخواست حذف ویس ✖':
                    if await exists_obj(user.database.deletes_user):
                        await user.send_message('درخواست قبلی شما در حال بررسی است ⚠')
                    else:
                        user.database.menu = 8
                        await user.send_message('لطفا ویس مورد نظر را ارسال کنید .', keyboards.per_back)
                elif text == 'ویس های شخصی 🔒':
                    user.database.menu = 11
                    await user.send_message('یکی از گزینه های زیر را انتخاب کنید .', keyboards.private)
                elif text == 'علاقه مندی ها ❤️':
                    user.database.menu = 15
                    await user.send_message('یکی از گزینه هارا انتخاب کنید .', keyboards.private)
                elif 'voice' in message:
                    if search_result := await functions.get_voice(message['voice']['file_unique_id']):
                        target_voice_name = search_result.name
                        await user.send_message(
                            f'نام ویس : {target_voice_name}\n\nشما میتوانید با تایپ\n\n'
                            f'@Persian_Meme_Bot {target_voice_name}\n\n از این ویس استفاده کنید 😁',
                            keyboards.use(target_voice_name)
                        )
                    else:
                        await user.send_message('نتونستم این ویس رو پیدا کنم ☹')
                else:
                    await user.send_message('دستور ناشناخته ⚠')
            elif user.database.menu == 2:
                user.database.menu = 1
                if text == 'بازگشت 🔙':
                    await user.send_message('شما به منوی اصلی بازگشتید 🔙', keyboards.user)
                else:
                    owner = await classes.User(request.http_session, instance=await functions.get_owner())
                    await owner.send_message(
                        f'New Message from {user.database.chat_id} 👇\n\n {text}',
                        keyboards.message(user.database.chat_id)
                    )
                    user.database.sent_message = True
                    await user.send_message('پیام شما به مدیریت ارسال شد ✔', keyboards.user, message_id)
            elif user.database.menu == 3:
                if text == 'بازگشت 🔙':
                    user.database.menu = 1
                    await user.send_message('شما به منوی اصلی بازگشتید 🔙', keyboards.user)
                elif text:
                    if len(text) > 50:
                        await user.send_message('نام ویس بیش از حد طولانی است ❌')
                    else:
                        user.database.menu = 4
                        user.database.temp_voice_name = text
                        await user.send_message('لطفا ویس مورد نظر را ارسال کنید .')
                else:
                    await user.send_message('لطفا یک متن به عنوان اسم ویس وارد کنید ⚠')
            elif user.database.menu == 4:
                if text == 'بازگشت 🔙':
                    user.database.menu = 3
                    await user.send_message('لطفا نام ویس مورد نظر را ارسال کنید !')
                else:
                    if 'voice' in message:
                        if target_voice := await functions.add_voice(
                                message['voice']['file_id'],
                                message['voice']['file_unique_id'],
                                user.database.temp_voice_name,
                                user.database,
                                'p'
                        ):
                            user.database.sent_voice = True
                            user.database.menu = 1
                            target_voice.message_id = await target_voice.send_voice(request.http_session)
                            await tasks.create_check_voice(target_voice.voice_id)
                            await user.send_message(
                                'ویس پیشنهادی شما برای تایید به مدیریت ارسال شد ✅', keyboards.user
                            )

                            await save_obj(target_voice)
                        else:
                            await user.send_message('این ویس در ربات موجود میباشد ⚠', reply_to_message_id=message_id)
                    else:
                        await user.send_message('لطفا یک ویس ارسال کنید ⚠')
            elif user.database.menu == 5:
                if text == 'بازگشت 🔙':
                    user.database.menu = 1
                    await user.send_message('شما به منوی اصلی بازگشتید 🔙', keyboards.user)
                else:
                    if 'voice' in message:
                        if await user.remove_voice(message['voice']['file_unique_id']):
                            user.database.menu = 1
                            await user.send_message('ویس شما با موفقیت حذف شد 🗑', keyboards.user)
                        else:
                            await user.send_message('ویس ارسالی متعلق به شما نبوده و یا در ربات موجود نمیباشد ❌')
                    else:
                        await user.send_message('لطفا یک ویس ارسال کنید 🔴')
            elif user.database.menu == 6:
                if text == 'بازگشت 🔙':
                    user.database.menu = 1
                    await user.send_message('شما به منوی اصلی بازگشتید 🔙', keyboards.user)
                elif text == 'روشن 🔛':
                    user.database.vote = True
                    user.database.menu = 1
                    await user.send_message('سیستم امتیازدهی برای شما روشن شد 🔛', keyboards.user)
                elif text == 'خاموش 🔴':
                    user.database.vote = False
                    user.database.menu = 1
                    await user.send_message('سیستم امتیازدهی برای شما خاموش شد 🔴', keyboards.user)
                else:
                    await user.send_message('انتخاب نامعتبر ⚠')
            elif user.database.menu == 7:
                if text == 'بازگشت 🔙':
                    user.database.menu = 1
                    await user.send_message('شما به منوی اصلی بازگشتید 🔙', keyboards.user)
                elif text == 'جدید به قدیم':
                    user.database.voice_order = '-voice_id'
                    user.database.menu = 1
                    await user.send_message('مرتب سازی ویس های تغییر کرد ✅', keyboards.user)
                elif text == 'قدیم به جدید':
                    user.database.voice_order = 'voice_id'
                    user.database.menu = 1
                    await user.send_message('مرتب سازی ویس های تغییر کرد ✅', keyboards.user)
                elif text == 'بهترین به بدترین':
                    user.database.voice_order = '-votes'
                    user.database.menu = 1
                    await user.send_message('مرتب سازی ویس های تغییر کرد ✅', keyboards.user)
                elif text == 'بدترین به بهترین':
                    user.database.voice_order = 'votes'
                    user.database.menu = 1
                    await user.send_message('مرتب سازی ویس های تغییر کرد ✅', keyboards.user)
                else:
                    await user.send_message('دستور نامعتبر ⚠')
            elif user.database.menu == 8:
                if text == 'بازگشت 🔙':
                    user.database.menu = 1
                    await user.send_message('شما به منوی اصلی بازگشتید 🔙', keyboards.user)
                else:
                    if 'voice' in message and (target_voice := await functions.get_voice(
                            message['voice']['file_unique_id']
                    )):
                        owner = await classes.User(request.http_session, instance=await functions.get_owner())
                        user.database.menu = 1
                        await user.send_message('درخواست شما با موفقیت ثبت شد ✅', keyboards.user, message_id)
                        await user.delete_request(target_voice)
                        await owner.send_message('New delete request 🗑')
                    else:
                        await user.send_message('لطفا یک ویس ارسال کنید ⚠')
            elif user.database.menu == 11:
                if text == 'بازگشت 🔙':
                    user.database.menu = 1
                    await user.send_message('شما به منوی اصلی بازگشتید 🔙', keyboards.user)
                elif text == 'افزودن ⏬':
                    if await user.private_user_count() <= 30:
                        user.database.menu = 12
                        await user.send_message('لطفا نام ویس را ارسال کنید .', keyboards.per_back)
                    else:
                        await user.send_message('شما حداکثر تعداد ویس های شخصی را ارسال کرده اید ⚠️')
                elif text == 'حذف 🗑':
                    user.database.menu = 13
                    await user.send_message('ویس مورد نظر را ارسال کنید .', keyboards.per_back)
                else:
                    await user.send_message('دستور نامعتبر ⚠️')
            elif user.database.menu == 12:
                if text == 'بازگشت 🔙':
                    user.database.menu = 11
                    await user.send_message('یکی از گزینه هارا انتخاب کنید .', keyboards.private)
                else:
                    if text:
                        if len(text) > 50:
                            await user.send_message('نام طولانی تر از حد مجاز است ❌')
                        else:
                            user.database.temp_voice_name = text
                            user.database.menu = 14
                            await user.send_message('لطفا ویس را ارسال کنید .')
                    else:
                        await user.send_message('لطفا یک نام وارد کنید ⚠️')
            elif user.database.menu == 13:
                if text == 'بازگشت 🔙':
                    user.database.menu = 11
                    await user.send_message('یکی از گزینه هارا انتخاب کنید .', keyboards.private)
                else:
                    if 'voice' in message and (current_voice := await functions.get_voice(
                            message['voice']['file_unique_id'], voice_type='p'
                    )):
                        if await user.delete_private_voice(current_voice):
                            user.database.menu = 11
                            await user.send_message('ویس مورد نظر از ربات حذف شد !', keyboards.private)
                        else:
                            await user.send_message('ویس مورد نظر از ویس های شخصی شما نیست ❌')
                    else:
                        await user.send_message('ویس ارسالی معتبر نیست ❌')
            elif user.database.menu == 14:
                if text == 'بازگشت 🔙':
                    user.database.menu = 12
                    await user.send_message('نام ویس را ارسال کنید .')
                else:
                    if 'voice' in message:
                        if not await functions.get_voice(message['voice']['file_unique_id']):
                            await user.create_private_voice(message)
                            user.database.menu = 11
                            await user.send_message('این ویس به لیست ویس های شما اضافه شد ✅', keyboards.private)
                        else:
                            await user.send_message('این ویس در ربات موجود است ❌')
                    else:
                        await user.send_message('لطفا یک ویس ارسال کنید ✖️')
            elif user.database.menu == 15:
                if text == 'بازگشت 🔙':
                    user.database.menu = 1
                    await user.send_message('شما به منوی اصلی بازگشتید 🔙', keyboards.user)
                elif text == 'افزودن ⏬':
                    if await user.count_favorite_voices() <= 30:
                        user.database.menu = 16
                        await user.send_message('لطفا ویس مورد نظر را ارسال کنید .', keyboards.per_back)
                    else:
                        await user.send_message('شما حداکثر تعداد ویس های مورد علاقه را اضافه کرده اید ⚠️')
                elif text == 'حذف 🗑':
                    user.database.menu = 17
                    await user.send_message('ویس مورد نظر را ارسال کنید .', keyboards.per_back)
                else:
                    await user.send_message('دستور نامعتبر ⚠️')
            elif user.database.menu == 16:
                if text == 'بازگشت 🔙':
                    user.database.menu = 15
                    await user.send_message('🔙', keyboards.private)
                else:
                    if 'voice' in message:
                        if current_voice := await functions.get_voice(message['voice']['file_unique_id']):
                            if await user.add_favorite_voice(current_voice):
                                user.database.menu = 15
                                await user.send_message(
                                    'ویس مورد نظر به لیست علاقه مندی های شما اضافه شد ✔️',
                                    keyboards.private
                                )
                            else:
                                await user.send_message('ویس در لیست موجود است ❌')
                        else:
                            await user.send_message('این ویس در ربات موجود نیست ❌')
                    else:
                        await user.send_message('لطفا یک ویس ارسال کنید !')
            elif user.database.menu == 17:
                if text == 'بازگشت 🔙':
                    user.database.menu = 15
                    await user.send_message('🔙', keyboards.private)
                else:
                    if 'voice' in message:
                        if current_voice := await functions.get_voice(message['voice']['file_unique_id']):
                            await user.delete_favorite_voice(current_voice)
                            user.database.menu = 15
                            await user.send_message('ویس از لیست حذف شد !', keyboards.private)
                        else:
                            await user.send_message('این ویس در ربات موجود نیست !')
                    else:
                        await user.send_message('لطفا یک ویس ارسال کنید !')
        await user.save()
    return HttpResponse(status=200)


async def webhook(request):
    async with aiohttp.ClientSession() as http_session:
        request.http_session = http_session
        return await webhook_view(request)
