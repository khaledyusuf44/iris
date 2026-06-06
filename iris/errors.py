"""Exceptions raised by the Iris engine."""


class IrisError(Exception):
    """Base exception for Iris engine failures."""


class IrisAPIError(IrisError):
    """Raised when the model endpoint cannot complete a request."""


class IrisResponseError(IrisError):
    """Raised when the model response cannot be parsed into the expected JSON."""
