from persianmeme.functions import edit_message_reply_markup
from persianmeme.models import Report, Meme, User
from persianmeme.classes import User as UserClass
from django.db.models import F
from persianmeme import translations
from django.utils.timezone import now
from django.conf import settings
from persianmeme.keyboards import dismissed, deleted


def handler(command: str, query_id: str, message_id: int, answer_query, report: Report, inliner: UserClass):
    if command == 'rep_accept':
        if report.meme.status == Meme.Status.PENDING:
            report.meme.delete_vote(inliner.session)
        report.meme.previous_status = report.meme.status
        report.meme.status = Meme.Status.REPORTED
        report.meme.save()
        report.meme.sender.report_violation_count = F('report_violation_count') + 1
        report.meme.sender.save()
        report.meme.sender.refresh_from_db()
        sender = UserClass(inliner.session, UserClass.Mode.NORMAL, instance=report.meme.sender)
        if sender.database.report_violation_count >= settings.VIOLATION_REPORT_LIMIT:
            sender.database.status = User.Status.BANNED
            sender.database.save()
            sender.send_message(translations.user_messages['you_are_banned'])
        else:
            sender.send_message(
                translations.user_messages['meme_violated'].format(
                    translations.user_messages[report.meme.type_string],
                    report.meme.name,
                    sender.database.report_violation_count,
                    settings.VIOLATION_REPORT_LIMIT
                ), parse_mode='HTML'
            )
        answer_query(query_id, translations.admin_messages['deleted'], True)
        edit_message_reply_markup(
            settings.MEME_REPORTS_CHANNEL, deleted, message_id, session=inliner.session
        )
    else:
        if report.meme.status == Meme.Status.REPORTED:
            if report.meme.previous_status == Meme.Status.PENDING:
                report.meme.send_vote(inliner.session)
            report.meme.status = report.meme.previous_status
            report.meme.save()
        answer_query(query_id, translations.admin_messages['report_dismissed'], False)
        edit_message_reply_markup(settings.MEME_REPORTS_CHANNEL, dismissed, message_id, session=inliner.session)
    report.status = Report.Status.REVIEWED
    report.review_date = now()
    report.save()
