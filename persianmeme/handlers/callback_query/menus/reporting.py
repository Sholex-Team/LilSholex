from persianmeme.models import Meme
from persianmeme.classes import User as UserClass
from LilSholex.exceptions import RequestInterruption
from persianmeme.types import ReportResult
from persianmeme.translations import user_messages


def handler(meme_id: int, query_id: str, answer_query, inliner: UserClass):
    try:
        meme = Meme.objects.get(id=meme_id, status=Meme.Status.PENDING)
    except (Meme.DoesNotExist, ValueError):
        inliner.database.save()
        raise RequestInterruption()
    match inliner.report_meme(meme):
        case ReportResult.REPORTED:
            answer_query(query_id, user_messages['report_submitted'], True)
        case ReportResult.REPORTED_BEFORE:
            answer_query(query_id, user_messages['reported_before'].format(user_messages[meme.type_string]), True)
        case ReportResult.REPORT_FAILED:
            answer_query(query_id, user_messages['report_reviewed'].format(user_messages[meme.type_string]), True)
