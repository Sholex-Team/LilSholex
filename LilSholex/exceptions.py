class TooManyRequests(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after

    def __str__(self):
        return f"Too many requests, retry after {self.retry_after} seconds !"


class RequestInterruption(Exception):
    pass

