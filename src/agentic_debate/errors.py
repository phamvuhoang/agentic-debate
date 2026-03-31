"""Error types for the neutral debate package."""


class DebateError(Exception):
    """Base exception for debate package errors."""


class DebateConfigurationError(DebateError):
    """Raised when a debate specification or compiled plan is invalid."""


class DebateExecutionError(DebateError):
    """Raised when a debate run fails during execution."""
