from persianmeme.models import Meme
from LilSholex.exceptions import RequestInterruption
from persianmeme.types import ReportResult
from persianmeme.translations import user_messages
from LilSholex.context import telegram as telegram_context
from persianmeme import context as meme_context
from LilSholex.functions import answer_callback_query


async def handler():
    try:
        meme = await Meme.objects.aget(id=meme_context.common.MEME_ID.get(), status=Meme.Status.PENDING)
    except (Meme.DoesNotExist, ValueError):
        await telegram_context.common.USER.get().database.asave()
        raise RequestInterruption()
    match await telegram_context.common.USER.get().report_meme(meme):
        case ReportResult.REPORTED:
            await answer_callback_query(user_messages['report_submitted'], True)
        case ReportResult.REPORTED_BEFORE:
            await answer_callback_query(user_messages['reported_before'].format(user_messages[meme.type_string]), True)
        case ReportResult.REPORT_FAILED:
            await answer_callback_query(user_messages['report_reviewed'].format(user_messages[meme.type_string]), True)
