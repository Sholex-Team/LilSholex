from enum import Enum, unique, auto


@unique
class ObjectType(Enum):
    PLAYLIST_VOICE = '1'
    PLAYLIST = '2'
    PRIVATE_VOICE = '3'
    FAVORITE_VOICE = '4'
    SUGGESTED_VOICE = '5'


class InvalidVoiceTag(ValueError):
    def __str__(self):
        return 'invalid_voice_tag'


class LongVoiceTag(ValueError):
    def __str__(self):
        return 'long_voice_tag'


class TooManyVoiceTags(ValueError):
    def __str__(self):
        return 'too_many_voice_tags'
