import pandas as pd
from app.engine.tools.profiling import DatasetProfilingTool
from app.engine.tools.validation import DataValidationTool
from app.engine.tools.aggregation import GroupedAggregationTool
from app.engine.tools.timeseries import TimeSeriesAnalysisTool


def test_dataset_profiling_tool():
    """Test DatasetProfilingTool computes accurate statistics and handles empty data."""
    tool = DatasetProfilingTool()
    df = pd.DataFrame({
        "sales": [100.0, 200.0, None, 400.0, 100.0],
        "category": ["A", "B", "A", "B", "A"],
    })

    res = tool.execute(df, parameters={})
    assert res.success is True
    data = res.data
    assert data["row_count"] == 5
    assert data["missing_values"]["sales"] == 1
    assert data["missing_values"]["category"] == 0
    assert data["unique_counts"]["category"] == 2
    assert "sales" in data["numeric_summary"]
    assert data["numeric_summary"]["sales"]["mean"] == 200.0
    assert data["numeric_summary"]["sales"]["min"] == 100.0
    assert data["numeric_summary"]["sales"]["max"] == 400.0

    # Empty dataframe
    empty_res = tool.execute(pd.DataFrame(columns=["a", "b"]), parameters={})
    assert empty_res.success is True
    assert empty_res.data["row_count"] == 0


def test_data_validation_tool():
    """Test DataValidationTool detects missing values, duplicates, and negative numbers."""
    tool = DataValidationTool()
    df = pd.DataFrame({
        "sales": [100.0, -50.0, 200.0, 100.0],
        "region": ["North", None, "South", "North"],
    })

    # Validate with non-negative rule on sales
    res = tool.execute(df, parameters={"non_negative_columns": ["sales"]})
    assert res.success is True
    data = res.data
    assert data["total_rows"] == 4
    assert data["missing_by_column"]["region"] == 1
    # Check negative value issue detected
    issue_types = [issue["type"] for issue in data["issues"]]
    assert "negative_values" in issue_types
    assert "missing_values" in issue_types


def test_grouped_aggregation_tool():
    """Test GroupedAggregationTool groups by dimension and aggregates metrics."""
    tool = GroupedAggregationTool()
    df = pd.DataFrame({
        "region": ["North", "North", "South", "South"],
        "sales": [100.0, 300.0, 50.0, 150.0],
        "units": [10, 30, 5, 15],
    })

    # Group by region
    res = tool.execute(
        df,
        parameters={
            "group_by": ["region"],
            "aggregations": {"sales": ["sum", "mean", "count"]},
        },
    )
    assert res.success is True
    groups = res.data["groups"]
    assert len(groups) == 2
    north = next(g for g in groups if g["region"] == "North")
    assert north["sales_sum"] == 400.0
    assert north["sales_mean"] == 200.0
    assert north["sales_count"] == 2

    # Overall aggregation without group_by
    overall_res = tool.execute(
        df,
        parameters={"metric_column": "sales", "agg_funcs": ["sum", "min", "max"]},
    )
    assert overall_res.success is True
    summary = overall_res.data["overall_summary"]["sales"]
    assert summary["sum"] == 600.0
    assert summary["min"] == 50.0
    assert summary["max"] == 300.0


def test_timeseries_analysis_tool():
    """Test TimeSeriesAnalysisTool aggregates by date, computes trend and period change."""
    tool = TimeSeriesAnalysisTool()
    df = pd.DataFrame({
        "date": [
            "2026-01-15", "2026-01-20",
            "2026-02-10", "2026-02-25",
            "2026-03-05", "2026-03-15",
        ],
        "sales": [1000.0, 1500.0, 800.0, 700.0, 500.0, 400.0],
    })

    res = tool.execute(
        df,
        parameters={
            "date_column": "date",
            "metric_column": "sales",
            "frequency": "ME",
            "agg_func": "sum",
        },
    )
    assert res.success is True
    data = res.data
    assert data["period_count"] == 3
    # Jan = 2500, Feb = 1500, Mar = 900 -> decreasing trend!
    assert "decreasing" in data["trend_direction"]
    assert data["overall_change_pct"] < 0

    periods = data["periods"]
    assert periods[0]["value"] == 2500.0
    assert periods[1]["value"] == 1500.0
    assert periods[1]["change"] == -1000.0
    assert periods[2]["value"] == 900.0
    assert periods[2]["change"] == -600.0
