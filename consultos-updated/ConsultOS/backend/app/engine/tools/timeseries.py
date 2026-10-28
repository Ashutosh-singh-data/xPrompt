from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from app.engine.tools.base import BaseTool
from app.engine.schemas import ToolExecutionResult


class TimeSeriesAnalysisTool(BaseTool):
    """Tool for time-series analysis: date-based trends, period-over-period change, and missing periods."""

    name = "timeseries_analyzer"
    description = (
        "Aggregates metrics over temporal periods (daily, weekly, monthly), calculates "
        "period-over-period growth/decline, evaluates trends, and identifies missing intervals."
    )

    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        available_columns: Optional[List[str]] = None,
    ) -> List[str]:
        errors = []
        date_col = parameters.get("date_column")
        metric_col = parameters.get("metric_column")

        if not date_col:
            errors.append("Parameter 'date_column' is required.")
        elif available_columns and date_col not in available_columns:
            errors.append(f"Date column '{date_col}' not found in dataset.")

        if not metric_col:
            errors.append("Parameter 'metric_column' is required.")
        elif available_columns and metric_col not in available_columns:
            errors.append(f"Metric column '{metric_col}' not found in dataset.")

        freq = parameters.get("frequency", "M")
        valid_freqs = {"D", "W", "M", "ME", "MS", "Q", "Y", "YE"}
        if freq.upper() not in valid_freqs:
            errors.append(f"Invalid frequency '{freq}'. Allowed: {sorted(valid_freqs)}")

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
                    data={
                        "periods": [],
                        "trend_direction": "insufficient_data",
                        "missing_periods": [],
                        "overall_change_pct": 0.0,
                    },
                    metadata={"empty": True},
                )

            date_col = parameters["date_column"]
            metric_col = parameters["metric_column"]
            raw_freq = parameters.get("frequency", "ME").upper()
            agg_func = parameters.get("agg_func", "sum").lower()

            # Normalize frequency for pandas
            if raw_freq == "M":
                freq = "ME"
            elif raw_freq == "Y":
                freq = "YE"
            else:
                freq = raw_freq

            # Work on clean copy with parsed datetime
            work_df = df.copy()
            work_df[date_col] = pd.to_datetime(work_df[date_col], errors="coerce")
            work_df = work_df.dropna(subset=[date_col])

            if len(work_df) == 0:
                return ToolExecutionResult(
                    tool_name=self.name,
                    success=False,
                    error=f"No valid dates could be parsed in column '{date_col}'.",
                )

            work_df[metric_col] = pd.to_numeric(work_df[metric_col], errors="coerce")
            work_df = work_df.dropna(subset=[metric_col])

            if len(work_df) == 0:
                return ToolExecutionResult(
                    tool_name=self.name,
                    success=False,
                    error=f"No numeric values available in metric column '{metric_col}'.",
                )

            # Resample and aggregate
            work_df = work_df.set_index(date_col)
            if agg_func == "mean":
                resampled = work_df[metric_col].resample(freq).mean()
            else:
                resampled = work_df[metric_col].resample(freq).sum()

            # Find missing periods (periods where count was 0 before fillna)
            counts = work_df[metric_col].resample(freq).count()
            missing_periods = [
                idx.strftime("%Y-%m-%d") for idx, cnt in counts.items() if cnt == 0
            ]

            resampled = resampled.fillna(0.0)

            periods_data: List[Dict[str, Any]] = []
            prev_val = None

            for timestamp, val in resampled.items():
                period_str = timestamp.strftime("%Y-%m-%d")
                val_float = round(float(val), 4)

                if prev_val is not None:
                    diff = round(val_float - prev_val, 4)
                    if prev_val != 0:
                        pct = round(((val_float - prev_val) / abs(prev_val)) * 100, 2)
                    else:
                        pct = 100.0 if val_float > 0 else 0.0
                else:
                    diff = None
                    pct = None

                periods_data.append({
                    "period": period_str,
                    "value": val_float,
                    "change": diff,
                    "pct_change": pct,
                })
                prev_val = val_float

            # Determine overall trend
            if len(periods_data) < 2:
                trend = "insufficient_data"
                overall_change_pct = 0.0
            else:
                first_val = periods_data[0]["value"]
                last_val = periods_data[-1]["value"]
                if first_val != 0:
                    overall_change_pct = round(((last_val - first_val) / abs(first_val)) * 100, 2)
                else:
                    overall_change_pct = 0.0

                changes = [p["change"] for p in periods_data[1:] if p["change"] is not None]
                pos_changes = sum(1 for c in changes if c > 0)
                neg_changes = sum(1 for c in changes if c < 0)

                if len(changes) > 0 and pos_changes == len(changes):
                    trend = "consistently_increasing"
                elif len(changes) > 0 and neg_changes == len(changes):
                    trend = "consistently_decreasing"
                elif overall_change_pct > 5.0:
                    trend = "increasing"
                elif overall_change_pct < -5.0:
                    trend = "decreasing"
                else:
                    trend = "stable"

            # Max and min periods
            sorted_periods = sorted(periods_data, key=lambda p: p["value"])
            min_period = sorted_periods[0] if sorted_periods else None
            max_period = sorted_periods[-1] if sorted_periods else None

            return ToolExecutionResult(
                tool_name=self.name,
                success=True,
                data={
                    "frequency": freq,
                    "period_count": len(periods_data),
                    "periods": periods_data,
                    "trend_direction": trend,
                    "overall_change_pct": overall_change_pct,
                    "missing_periods": missing_periods,
                    "min_period": min_period,
                    "max_period": max_period,
                },
                metadata={
                    "date_column": date_col,
                    "metric_column": metric_col,
                },
            )

        except Exception as exc:
            return ToolExecutionResult(
                tool_name=self.name,
                success=False,
                error=f"Time-series analysis failed: {str(exc)}",
            )
