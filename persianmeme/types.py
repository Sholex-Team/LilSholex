from enum import Enum, unique, auto


@unique
class ObjectType(Enum):
    PLAYLIST_VOICE = '1'
    PLAYLIST = '2'
    PRIVATE_VOICE = '3'
    SUGGESTED_VOICE = '5'
    SUGGESTED_VIDEO = '6'
    SUGGESTED_MEME = '7'


class InvalidMemeTag(ValueError):
    def __str__(self):
        return 'invalid_meme_tag'


class LongMemeTag(ValueError):
    def __str__(self):
        return 'long_meme_tag'


class TooManyMemeTags(ValueError):
    def __str__(self):
        return 'too_many_meme_tags'


@unique
class ReportResult(Enum):
    REPORTED = auto()
    REPORTED_BEFORE = auto()
    REPORT_FAILED = auto()


@unique
class SearchType(Enum):
    NAMES = auto()
    TAGS = auto()
    ALL = auto()
