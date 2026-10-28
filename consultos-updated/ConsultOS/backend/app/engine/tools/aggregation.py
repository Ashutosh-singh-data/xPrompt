from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
from app.engine.tools.base import BaseTool
from app.engine.schemas import ToolExecutionResult

SUPPORTED_AGG_FUNCS = {"sum", "mean", "median", "min", "max", "count", "std"}


class GroupedAggregationTool(BaseTool):
    """Tool for grouped and overall aggregations on tabular metrics."""

    name = "grouped_aggregator"
    description = (
        "Computes grouped or overall aggregations (sum, mean, median, min, max, count, std) "
        "across specified dimensions and metric columns."
    )

    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        available_columns: Optional[List[str]] = None,
    ) -> List[str]:
        errors = []

        # Validate group_by
        group_by = parameters.get("group_by")
        if group_by is not None:
            if isinstance(group_by, str):
                group_cols = [group_by]
            elif isinstance(group_by, list):
                group_cols = group_by
            else:
                errors.append("Parameter 'group_by' must be a string or list of column names.")
                group_cols = []

            if available_columns:
                missing = [c for c in group_cols if c not in available_columns]
                if missing:
                    errors.append(f"Group-by columns not found in dataset: {missing}")

        # Validate aggregations
        # Can be provided as {"sales": ["sum", "mean"]} or metric_column + agg_funcs
        aggregations = parameters.get("aggregations")
        metric_column = parameters.get("metric_column")

        if aggregations is None and metric_column is None:
            errors.append("Must specify either 'aggregations' dictionary or 'metric_column'.")

        if aggregations is not None:
            if not isinstance(aggregations, dict):
                errors.append("Parameter 'aggregations' must be a dictionary mapping column to functions.")
            else:
                for col, funcs in aggregations.items():
                    if available_columns and col not in available_columns:
                        errors.append(f"Aggregation column '{col}' not found in dataset.")
                    func_list = [funcs] if isinstance(funcs, str) else funcs
                    if not isinstance(func_list, list):
                        errors.append(f"Aggregation functions for '{col}' must be a list or string.")
                    else:
                        for fn in func_list:
                            if fn.lower() not in SUPPORTED_AGG_FUNCS:
                                errors.append(f"Unsupported aggregation function '{fn}'. Allowed: {sorted(SUPPORTED_AGG_FUNCS)}")

        if metric_column is not None:
            if available_columns and metric_column not in available_columns:
                errors.append(f"Metric column '{metric_column}' not found in dataset.")
            agg_funcs = parameters.get("agg_funcs", ["sum", "mean", "count"])
            func_list = [agg_funcs] if isinstance(agg_funcs, str) else agg_funcs
            for fn in func_list:
                if fn.lower() not in SUPPORTED_AGG_FUNCS:
                    errors.append(f"Unsupported aggregation function '{fn}'. Allowed: {sorted(SUPPORTED_AGG_FUNCS)}")

        return errors

    def execute(
        self,
        df: pd.DataFrame,
        parameters: Dict[str, Any],
    ) -> ToolExecutionResult:
        try:
            if df.empty:
                return ToolExecutionResult(
                    tool_name=self.name,
                    success=True,
                    data={"groups": [], "total_groups": 0, "summary": "Dataset is empty."},
                    metadata={"empty": True},
                )

            # Normalize group_by
            raw_group_by = parameters.get("group_by")
            if raw_group_by:
                group_cols = [raw_group_by] if isinstance(raw_group_by, str) else list(raw_group_by)
            else:
                group_cols = []

            # Normalize aggregation spec
            raw_aggs = parameters.get("aggregations")
            metric_col = parameters.get("metric_column")

            agg_dict: Dict[str, List[str]] = {}
            if raw_aggs and isinstance(raw_aggs, dict):
                for col, funcs in raw_aggs.items():
                    agg_dict[col] = [funcs] if isinstance(funcs, str) else list(funcs)
            elif metric_col:
                raw_funcs = parameters.get("agg_funcs", ["sum", "mean", "count"])
                agg_dict[metric_col] = [raw_funcs] if isinstance(raw_funcs, str) else list(raw_funcs)

            # Ensure numeric conversion where possible
            work_df = df.copy()
            for col in agg_dict:
                if col in work_df.columns:
                    work_df[col] = pd.to_numeric(work_df[col], errors="coerce")

            # Perform aggregation
            if group_cols:
                # Grouped aggregation
                grouped = work_df.groupby(group_cols, dropna=False)

                # Build named aggregations
                agg_expressions = {}
                for col, funcs in agg_dict.items():
                    for fn in funcs:
                        fn_clean = fn.lower()
                        col_alias = f"{col}_{fn_clean}"
                        if fn_clean == "median":
                            agg_expressions[col_alias] = (col, lambda s: s.median())
                        else:
                            agg_expressions[col_alias] = (col, fn_clean)

                result_df = grouped.agg(**agg_expressions).reset_index()

                # Sorting and limiting
                sort_by = parameters.get("sort_by")
                ascending = bool(parameters.get("ascending", False))
                if sort_by and sort_by in result_df.columns:
                    result_df = result_df.sort_values(by=sort_by, ascending=ascending)
                elif len(agg_expressions) > 0:
                    # Default sort by first aggregated metric descending
                    first_metric = list(agg_expressions.keys())[0]
                    result_df = result_df.sort_values(by=first_metric, ascending=False)

                limit = parameters.get("limit")
                if limit and isinstance(limit, int) and limit > 0:
                    result_df = result_df.head(limit)

                # Convert records to JSON-compatible dicts
                # Replace NaNs with None
                records = result_df.replace({np.nan: None}).to_dict(orient="records")

                # Round floats
                for row in records:
                    for k, v in row.items():
                        if isinstance(v, float) and v is not None:
                            row[k] = round(v, 4)

                return ToolExecutionResult(
                    tool_name=self.name,
                    success=True,
                    data={
                        "groups": records,
                        "total_groups": len(records),
                        "grouped_by": group_cols,
                    },
                    metadata={"record_count": len(records)},
                )
            else:
                # Overall aggregations without grouping
                summary = {}
                for col, funcs in agg_dict.items():
                    series = work_df[col].dropna()
                    summary[col] = {}
                    for fn in funcs:
                        fn_clean = fn.lower()
                        if fn_clean == "sum":
                            val = float(series.sum())
                        elif fn_clean == "mean":
                            val = float(series.mean())
                        elif fn_clean == "median":
                            val = float(series.median())
                        elif fn_clean == "min":
                            val = float(series.min())
                        elif fn_clean == "max":
                            val = float(series.max())
                        elif fn_clean == "count":
                            val = int(series.count())
                        elif fn_clean == "std":
                            val = float(series.std()) if len(series) > 1 else 0.0
                        else:
                            val = None
                        summary[col][fn_clean] = round(val, 4) if isinstance(val, float) else val

                return ToolExecutionResult(
                    tool_name=self.name,
                    success=True,
                    data={"overall_summary": summary},
                    metadata={"grouped": False},
                )

        except Exception as exc:
            return ToolExecutionResult(
                tool_name=self.name,
                success=False,
                error=f"Grouped aggregation failed: {str(exc)}",
            )
