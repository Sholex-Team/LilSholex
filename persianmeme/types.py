from enum import Enum, unique, auto


@unique
class ObjectType(Enum):
    VOICE = auto()
    PLAYLIST = auto()

    @staticmethod
    def check_value(value: str):
        try:
            return ObjectType(int(value))
        except (ValueError, TypeError):
            return None
