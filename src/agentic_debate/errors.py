"""Error types for the neutral debate package."""


class DebateError(Exception):
    """Base exception for debate package errors."""


class DebateConfigurationError(DebateError):
    """Raised when a debate specification or compiled plan is invalid."""


class DebateExecutionError(DebateError):
    """Raised when a debate run fails during execution."""


class DebatePlanningError(DebateError):
    """Raised when planning a debate fails before execution begins."""

    def __init__(self, *, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage


class DebateGenerationError(DebateExecutionError):
    """Raised when generated debate content fails during execution."""

    def __init__(self, *, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage
