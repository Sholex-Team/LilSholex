from enum import Enum, unique, auto


@unique
class ObjectType(Enum):
    PLAYLIST_VOICE = auto()
    PLAYLIST = auto()
    PRIVATE_VOICE = auto()
    FAVORITE_VOICE = auto()
    SUGGESTED_VOICE = auto()

    @staticmethod
    def check_value(value: str):
        try:
            return ObjectType(int(value))
        except (ValueError, TypeError):
            return None


class InvalidVoiceTag(ValueError):
    def __str__(self):
        return 'invalid_voice_tag'


class LongVoiceTag(ValueError):
    def __str__(self):
        return 'long_voice_tag'


class TooManyVoiceTags(ValueError):
    def __str__(self):
        return 'too_many_voice_tags'
