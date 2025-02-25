from contextvars import ContextVar

VOTE_OPTION = ContextVar('VOTE_OPTION')
RATE_OPTION = ContextVar('RATE_OPTION')
CALLBACK_TYPE = ContextVar('CALLBACK_TYPE')
PAGE_TYPE = ContextVar('PAGE_TYPE')
PAGE = ContextVar('PAGE', default=1)
COMMAND = ContextVar('COMMAND')
MESSAGE_ID = ContextVar('MESSAGE_ID')
DELETE_REQUEST_ID = ContextVar('DELETE_REQUEST_ID')
