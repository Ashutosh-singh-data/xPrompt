from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from app.engine.tools.base import BaseTool
from app.engine.schemas import ToolExecutionResult


class DataValidationTool(BaseTool):
    """Tool for data validation: checks for missing values, duplicates, and invalid values."""

    name = "data_validator"
    description = (
        "Validates dataset health by detecting nulls, duplicate records, negative values "
        "in metric columns, and domain constraint violations."
    )

    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        available_columns: Optional[List[str]] = None,
    ) -> List[str]:
        errors = []
        target_columns = parameters.get("columns")
        if target_columns is not None:
            if not isinstance(target_columns, list):
                errors.append("Parameter 'columns' must be a list of column names.")
            elif available_columns:
                missing = [col for col in target_columns if col not in available_columns]
                if missing:
                    errors.append(f"Columns not found in dataset: {missing}")

        non_negative = parameters.get("non_negative_columns")
        if non_negative is not None:
            if not isinstance(non_negative, list):
                errors.append("Parameter 'non_negative_columns' must be a list.")
            elif available_columns:
                missing = [col for col in non_negative if col not in available_columns]
                if missing:
                    errors.append(f"Non-negative columns not found in dataset: {missing}")

        return errors

    def execute(
        self,
        df: pd.DataFrame,
        parameters: Dict[str, Any],
    ) -> ToolExecutionResult:
        try:
            target_cols = parameters.get("columns")
            data = df[target_cols] if target_cols and all(c in df.columns for c in target_cols) else df

            total_rows = int(len(data))
            if total_rows == 0:
                return ToolExecutionResult(
                    tool_name=self.name,
                    success=True,
                    data={
                        "total_rows": 0,
                        "duplicate_rows": 0,
                        "missing_by_column": {},
                        "issues": ["Dataset is empty."],
                        "is_valid": False,
                    },
                    metadata={"empty": True},
                )

            issues: List[Dict[str, Any]] = []

            # 1. Missing values check
            missing_by_col = {}
            for col in data.columns:
                missing_cnt = int(data[col].isna().sum())
                missing_by_col[col] = missing_cnt
                if missing_cnt > 0:
                    pct = round(float((missing_cnt / total_rows) * 100), 2)
                    issues.append({
                        "type": "missing_values",
                        "column": col,
                        "count": missing_cnt,
                        "percentage": pct,
                        "severity": "high" if pct > 20 else "medium",
                    })

            # 2. Duplicate rows check
            dup_count = int(data.duplicated().sum())
            if dup_count > 0:
                dup_pct = round(float((dup_count / total_rows) * 100), 2)
                issues.append({
                    "type": "duplicate_rows",
                    "count": dup_count,
                    "percentage": dup_pct,
                    "severity": "high" if dup_pct > 10 else "medium",
                })

            # 3. Non-negative constraints check
            non_negative_cols = parameters.get("non_negative_columns")
            if non_negative_cols:
                for col in non_negative_cols:
                    if col in data.columns and pd.api.types.is_numeric_dtype(data[col]):
                        negative_count = int((data[col] < 0).sum())
                        if negative_count > 0:
                            issues.append({
                                "type": "negative_values",
                                "column": col,
                                "count": negative_count,
                                "severity": "high",
                            })

            is_valid = not any(issue.get("severity") == "high" for issue in issues)

            return ToolExecutionResult(
                tool_name=self.name,
                success=True,
                data={
                    "total_rows": total_rows,
                    "duplicate_rows": dup_count,
                    "missing_by_column": missing_by_col,
                    "issues": issues,
                    "issue_count": len(issues),
                    "is_valid": is_valid,
                },
                metadata={"checked_columns": list(data.columns)},
            )
        except Exception as exc:
            return ToolExecutionResult(
                tool_name=self.name,
                success=False,
                error=f"Data validation failed: {str(exc)}",
            )
