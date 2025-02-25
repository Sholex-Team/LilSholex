from contextvars import ContextVar

BOT_TOKEN = ContextVar('BOT_TOKEN')
HTTP_SESSION = ContextVar('HTTP_SESSION')
USER_CHAT_ID = ContextVar('USER_CHAT_ID')
USER = ContextVar('USER')
CHAT_ID = ContextVar('CHAT_ID')
MESSAGE_ID = ContextVar('MESSAGE_ID')
