from persianmeme.functions import edit_message_reply_markup
from persianmeme.models import Report, Meme, User
from persianmeme.classes import User as UserClass
from django.db.models import F
from persianmeme import translations
from django.utils.timezone import now
from django.conf import settings
from persianmeme.keyboards import dismissed, deleted
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context
from persianmeme import context as meme_context
from LilSholex.functions import answer_callback_query


async def handler():
    report = meme_context.common.REPORT.get()
    if meme_context.callback_query.COMMAND.get() == 'rep_accept':
        async with TaskGroup() as tg:
            if report.meme.status == Meme.Status.PENDING:
                tg.create_task(report.meme.delete_vote())
            if report.meme.status != Meme.Status.REPORTED:
                report.meme.previous_status = report.meme.status
                report.meme.status = Meme.Status.REPORTED
                tg.create_task(report.meme.asave(update_fields=('previous_status', 'status')))
            report.meme.sender.report_violation_count = F('report_violation_count') + 1
            tg.create_task(report.meme.sender.asave(update_fields=('report_violation_count',)))
            tg.create_task(report.meme.sender.arefresh_from_db())
        sender = UserClass(instance=report.meme.sender)
        async with TaskGroup() as tg:
            if sender.database.report_violation_count >= settings.VIOLATION_REPORT_LIMIT:
                sender.database.status = User.Status.BANNED
                tg.create_task(sender.database.asave(update_fields=('status',)))
                tg.create_task(sender.send_message(translations.user_messages['you_are_banned']))
            else:
                tg.create_task(sender.send_message(
                    translations.user_messages['meme_violated'].format(
                        translations.user_messages[report.meme.type_string],
                        report.meme.name,
                        sender.database.report_violation_count,
                        settings.VIOLATION_REPORT_LIMIT
                    ), parse_mode='HTML'
                ))
            tg.create_task(answer_callback_query(translations.admin_messages['deleted'], True))
            tg.create_task(edit_message_reply_markup(settings.MEME_REPORTS_CHANNEL, deleted))
    else:
        async with TaskGroup() as tg:
            if report.meme.status == Meme.Status.REPORTED:
                if report.meme.previous_status == Meme.Status.PENDING:
                    await report.meme.send_vote()
                report.meme.status = report.meme.previous_status
                tg.create_task(report.meme.asave(update_fields=('status', 'task_id')))
            tg.create_task(answer_callback_query(translations.admin_messages['report_dismissed'], False))
            tg.create_task(edit_message_reply_markup(settings.MEME_REPORTS_CHANNEL, dismissed))
    report.status = Report.Status.REVIEWED
    report.reviewer = telegram_context.common.USER.get().database
    report.review_date = now()
    await report.asave()
