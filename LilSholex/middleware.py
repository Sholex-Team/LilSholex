from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.http import HttpRequest, HttpResponse
from django.conf import settings


class TelegramMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        request.is_from_telegram = request.META.get(settings.TELEGRAM_HEADER_NAME) == settings.WEBHOOK_TOKEN
        return self.get_response(request)


class ConditionalRequestMixin:
    def process_request(self, request: HttpRequest):
        if not request.is_from_telegram:
            return super().process_request(request)


class ConditionalResponseMixin:
    def process_response(self, request: HttpRequest, response: HttpResponse):
        if request.is_from_telegram:
            return response
        return super().process_response(request, response)


class CSessionMiddleware(ConditionalResponseMixin, ConditionalRequestMixin, SessionMiddleware):
    pass


class CAuthenticationMiddleware(ConditionalRequestMixin, AuthenticationMiddleware):
    pass


class CMessageMiddleware(ConditionalResponseMixin, ConditionalRequestMixin, MessageMiddleware):
    pass
