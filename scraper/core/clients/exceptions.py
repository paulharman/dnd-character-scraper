"""
Client-specific exceptions.
"""


class ClientError(Exception):
    """Base exception for client errors."""
    pass


class CharacterNotFoundError(ClientError):
    """Raised when character cannot be found."""
    def __init__(self, character_id: int, message: str = None):
        self.character_id = character_id
        if message is None:
            message = f"Character {character_id} not found"
        super().__init__(message)


class PrivateCharacterError(ClientError):
    """Raised when character is private and requires authentication."""
    def __init__(self, character_id: int, message: str = None):
        self.character_id = character_id
        if message is None:
            message = f"Character {character_id} is private - session cookie required"
        super().__init__(message)


class APIError(ClientError):
    """Raised when API returns an error."""
    def __init__(self, status_code: int, message: str = None):
        self.status_code = status_code
        if message is None:
            message = f"API error: HTTP {status_code}"
        super().__init__(message)


class ValidationError(ClientError):
    """Raised when character data fails validation."""
    pass


class RateLimitError(ClientError):
    """Raised when rate limit is exceeded."""
    def __init__(self, retry_after: int = None, message: str = None):
        self.retry_after = retry_after
        if message is None:
            message = f"Rate limit exceeded"
            if retry_after:
                message += f" - retry after {retry_after} seconds"
        super().__init__(message)


class TimeoutError(ClientError):
    """Raised when request times out."""
    pass