"""WundergroundPWS exceptions."""


class WundergroundPWSError(Exception):
    """Base class for WundergroundPWS errors."""

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status


class InvalidApiKeyError(WundergroundPWSError):
    """Raised when API Key format is invalid."""

class InvalidStationIdError(WundergroundPWSError):
    """Raised when Station ID format is invalid."""

class InvalidApiResponseError(WundergroundPWSError):
    """Raised when API response is invalid."""
