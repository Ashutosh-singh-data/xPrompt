from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
from app.engine.schemas import ToolExecutionResult


class BaseTool(ABC):
    """Abstract base class for all approved ConsultOS analytical tools."""

    name: str
    description: str

    @abstractmethod
    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        available_columns: Optional[List[str]] = None,
    ) -> List[str]:
        """Validate input parameters before execution.

        Returns a list of error strings if any parameters are invalid.
        """
        pass

    @abstractmethod
    def execute(
        self,
        df: pd.DataFrame,
        parameters: Dict[str, Any],
    ) -> ToolExecutionResult:
        """Execute analytical computation on the provided dataset."""
        pass
