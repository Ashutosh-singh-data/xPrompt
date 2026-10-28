from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from app.engine.tools.base import BaseTool
from app.engine.schemas import ToolExecutionResult


class DatasetProfilingTool(BaseTool):
    """Tool for dataset profiling: structural summary, data types, missing values, and statistics."""

    name = "dataset_profiler"
    description = (
        "Inspects a dataset and computes row counts, column types, missing values, "
        "distinct counts, duplicate rows, and numeric statistical distributions."
    )

    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        available_columns: Optional[List[str]] = None,
    ) -> List[str]:
        # Profiler accepts optional columns filter
        errors = []
        target_columns = parameters.get("columns")
        if target_columns is not None:
            if not isinstance(target_columns, list):
                errors.append("Parameter 'columns' must be a list of column names.")
            elif available_columns:
                missing = [col for col in target_columns if col not in available_columns]
                if missing:
                    errors.append(f"Columns not found in dataset: {missing}")
        return errors

    def execute(
        self,
        df: pd.DataFrame,
        parameters: Dict[str, Any],
    ) -> ToolExecutionResult:
        try:
            target_cols = parameters.get("columns")
            data = df[target_cols] if target_cols and all(c in df.columns for c in target_cols) else df

            row_count = int(len(data))
            col_count = int(len(data.columns))

            if row_count == 0:
                return ToolExecutionResult(
                    tool_name=self.name,
                    success=True,
                    data={
                        "row_count": 0,
                        "column_count": col_count,
                        "column_types": {col: str(dtype) for col, dtype in data.dtypes.items()},
                        "missing_values": {col: 0 for col in data.columns},
                        "missing_percentages": {col: 0.0 for col in data.columns},
                        "unique_counts": {col: 0 for col in data.columns},
                        "duplicate_rows": 0,
                        "numeric_summary": {},
                    },
                    metadata={"empty_dataset": True},
                )

            # Missing values
            missing_counts = {col: int(data[col].isna().sum()) for col in data.columns}
            missing_pct = {
                col: round(float((count / row_count) * 100), 2)
                for col, count in missing_counts.items()
            }

            # Unique counts
            unique_counts = {col: int(data[col].nunique(dropna=False)) for col in data.columns}

            # Duplicate rows
            duplicate_count = int(data.duplicated().sum())

            # Numeric distributions
            numeric_summary: Dict[str, Dict[str, Any]] = {}
            numeric_df = data.select_dtypes(include=[np.number])
            for col in numeric_df.columns:
                series = numeric_df[col].dropna()
                if len(series) > 0:
                    numeric_summary[col] = {
                        "count": int(len(series)),
                        "mean": round(float(series.mean()), 4),
                        "std": round(float(series.std()), 4) if len(series) > 1 else 0.0,
                        "min": round(float(series.min()), 4),
                        "q25": round(float(series.quantile(0.25)), 4),
                        "median": round(float(series.median()), 4),
                        "q75": round(float(series.quantile(0.75)), 4),
                        "max": round(float(series.max()), 4),
                    }

            column_types = {col: str(dtype) for col, dtype in data.dtypes.items()}

            return ToolExecutionResult(
                tool_name=self.name,
                success=True,
                data={
                    "row_count": row_count,
                    "column_count": col_count,
                    "column_types": column_types,
                    "missing_values": missing_counts,
                    "missing_percentages": missing_pct,
                    "unique_counts": unique_counts,
                    "duplicate_rows": duplicate_count,
                    "numeric_summary": numeric_summary,
                },
                metadata={"columns_analyzed": list(data.columns)},
            )
        except Exception as exc:
            return ToolExecutionResult(
                tool_name=self.name,
                success=False,
                error=f"Dataset profiling failed: {str(exc)}",
            )
