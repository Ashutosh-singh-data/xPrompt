from typing import Any, Optional


class ConsultOSException(Exception):
    """Base exception for all ConsultOS domain errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class ResourceNotFoundException(ConsultOSException):
    """Base exception for missing resources (HTTP 404)."""

    def __init__(
        self,
        message: str,
        code: str = "RESOURCE_NOT_FOUND",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=404,
            details=details,
        )


class InvestigationNotFoundException(ResourceNotFoundException):
    """Raised when an investigation is not found."""

    def __init__(self, investigation_id: str):
        super().__init__(
            message=f"Investigation '{investigation_id}' not found.",
            code="INVESTIGATION_NOT_FOUND",
            details={"investigation_id": investigation_id},
        )


class TaskNotFoundException(ResourceNotFoundException):
    """Raised when a task is not found."""

    def __init__(self, task_id: str):
        super().__init__(
            message=f"Task '{task_id}' not found.",
            code="TASK_NOT_FOUND",
            details={"task_id": task_id},
        )


class ReportNotReadyException(ConsultOSException):
    """Raised when an investigation exists but no report has been generated yet."""

    def __init__(self, investigation_id: str):
        super().__init__(
            message=f"Report is not ready. No report has been generated for investigation '{investigation_id}' yet.",
            code="REPORT_NOT_READY",
            status_code=404,
            details={"investigation_id": investigation_id},
        )


class InvalidRelationshipException(ConsultOSException):
    """Raised when cross-resource relationships are invalid or violate integrity rules."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="INVALID_RELATIONSHIP",
            status_code=400,
            details=details,
        )


class DatabaseConnectionError(ConsultOSException):
    """Raised when database connectivity cannot be established."""

    def __init__(self, message: str = "Database connection failed."):
        super().__init__(
            message=message,
            code="DATABASE_UNAVAILABLE",
            status_code=503,
        )
