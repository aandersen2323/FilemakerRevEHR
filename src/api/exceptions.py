"""Custom exceptions for RevolutionEHR API interactions."""


class RevEHRAPIError(Exception):
    """Base exception for RevolutionEHR API errors."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class RevEHRAuthError(RevEHRAPIError):
    """Authentication/authorization error."""
    pass


class RevEHRNotFoundError(RevEHRAPIError):
    """Resource not found error."""
    pass


class RevEHRValidationError(RevEHRAPIError):
    """Data validation error from API."""
    pass


class RevEHRRateLimitError(RevEHRAPIError):
    """Rate limit exceeded error."""
    pass
