class HttpRequestException(Exception):
    """Custom exception class to handle build the exception."""

    def __init__(self, uri: str, attempts: int, reason: str) -> None:
        super().__init__(f"Request Failed: Connection to {uri} failed after {attempts} attempt(s): {reason}")
