from django.utils.log import AdminEmailHandler
from django.conf import settings
from django.core.cache import cache


class ThrottledEmailHandler(AdminEmailHandler):
    def emit(self, record):
        try:
            if cache.incr(settings.ERROR_REPORT_CACHE_KEY) >= settings.ERROR_REPORT_THROTTLE_COUNT:
                return
        except ValueError:
            cache.add(settings.ERROR_REPORT_CACHE_KEY, 1, settings.ERROR_REPORT_THROTTLE_TIME)
        return super().emit(record)
