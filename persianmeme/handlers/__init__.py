from .callback_query import handlers as callback_query_handlers
from .inline_query import handlers as inline_query_handlers
from .message import handlers as message_handlers
from .chosen_inline_result import handlers as chosen_inline_result_handlers
from .channel_post import handlers as channel_post_handlers

__all__ = (
    'callback_query_handlers',
    'inline_query_handlers',
    'message_handlers',
    'chosen_inline_result_handlers',
    'channel_post_handlers'
)
