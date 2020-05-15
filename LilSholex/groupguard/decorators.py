from urllib3.exceptions import HTTPError
from json import JSONDecodeError


def fix(func):
    def check_exception(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except (HTTPError, JSONDecodeError):
                continue
    return check_exception
