import re
import uuid
from typing import List, Dict, Any, Optional, Tuple, Set
import pandas as pd
from app.engine.schemas import (
    InvestigationPlan,
    PlannedHypothesis,
    PlannedTask,
    DatasetProfile,
)


from app.core.exceptions import ConsultOSException


class UnsupportedQuestionError(ConsultOSException):
    """Raised when a business inquiry cannot be investigated using the provided dataset."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="UNSUPPORTED_QUESTION",
            status_code=422,
        )


COMMON_METRIC_KEYWORDS = {
    "sales", "revenue", "profit", "cost", "spend", "churn", "loss", "margin",
    "amount", "units", "quantity", "orders", "price", "conversion", "volume",
    "users", "customers", "clicks", "impressions", "rate", "score", "total"
}

COMMON_DATE_KEYWORDS = {
    "date", "timestamp", "time", "day", "month", "year", "week", "created_at",
    "order_date", "trans_date", "period"
}

COMMON_DIMENSION_KEYWORDS = {
    "category", "region", "segment", "tier", "channel", "product", "country",
    "city", "state", "brand", "customer_type", "type", "department", "division"
}


class RuleBasedPlanner:
    """Deterministic, rule-based planner that analyzes business questions and dataset schemas.

    Generates testable hypotheses and structured executable tasks without hallucinating columns.
    """

    def plan(
        self,
        business_question: str,
        columns: Optional[List[str]] = None,
        dataset_profile: Optional[DatasetProfile] = None,
        df: Optional[pd.DataFrame] = None,
    ) -> InvestigationPlan:
        """Create an investigation plan tailored to the question and available columns."""
        clean_question = business_question.strip()
        if not clean_question:
            raise ValueError("Business question cannot be empty.")

        # Determine available columns and dtypes
        available_columns, dtypes = self._resolve_dataset_info(
            columns=columns,
            dataset_profile=dataset_profile,
            df=df,
        )

        if not available_columns:
            raise UnsupportedQuestionError(
                "No columns available in dataset. Cannot generate an investigation plan."
            )

        # Classify dataset columns
        date_cols, metric_cols, dimension_cols = self._classify_columns(
            available_columns, dtypes
        )

        # Verify dataset can address question
        self._validate_question_dataset_compatibility(
            clean_question, available_columns, metric_cols, dimension_cols
        )

        # Select primary metric, date, and dimension
        primary_metric = self._select_primary_metric(clean_question, metric_cols)
        primary_date = date_cols[0] if date_cols else None
        primary_dim = self._select_primary_dimension(clean_question, dimension_cols)

        # Generate Hypotheses
        hypotheses = self._generate_hypotheses(
            clean_question, primary_metric, primary_dim, primary_date
        )

        # Generate Tasks
        tasks = self._generate_tasks(
            available_columns,
            primary_metric,
            primary_dim,
            primary_date,
            hypotheses,
        )

        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        return InvestigationPlan(
            plan_id=plan_id,
            business_question=clean_question,
            dataset_name=dataset_profile.name if dataset_profile else "primary_dataset",
            hypotheses=hypotheses,
            tasks=tasks,
        )

    def _resolve_dataset_info(
        self,
        columns: Optional[List[str]] = None,
        dataset_profile: Optional[DatasetProfile] = None,
        df: Optional[pd.DataFrame] = None,
    ) -> Tuple[List[str], Dict[str, str]]:
        if df is not None:
            return list(df.columns), {c: str(d) for c, d in df.dtypes.items()}
        if dataset_profile is not None:
            return dataset_profile.columns, dataset_profile.dtypes
        if columns is not None:
            return columns, {}
        return [], {}

    def _classify_columns(
        self,
        columns: List[str],
        dtypes: Dict[str, str],
    ) -> Tuple[List[str], List[str], List[str]]:
        date_cols: List[str] = []
        metric_cols: List[str] = []
        dimension_cols: List[str] = []

        for col in columns:
            col_lower = col.lower()
            dtype_str = dtypes.get(col, "").lower()

            # Date detection
            if any(k in col_lower for k in COMMON_DATE_KEYWORDS) or "datetime" in dtype_str:
                date_cols.append(col)
                continue

            # Metric detection
            is_numeric_type = any(t in dtype_str for t in ["int", "float", "number"])
            is_metric_name = any(k in col_lower for k in COMMON_METRIC_KEYWORDS)

            if is_numeric_type or is_metric_name:
                metric_cols.append(col)
            else:
                dimension_cols.append(col)

        # If no metric detected by keyword, treat remaining columns as dimensions
        if not metric_cols and dimension_cols:
            pass

        return date_cols, metric_cols, dimension_cols

    def _validate_question_dataset_compatibility(
        self,
        question: str,
        available_columns: List[str],
        metric_cols: List[str],
        dimension_cols: List[str],
    ) -> None:
        """Check if dataset has any reasonable relevance to the question."""
        q_words = set(re.findall(r"\w+", question.lower()))

        # If question asks about metrics but dataset has zero numeric/metric columns
        if not metric_cols and any(k in q_words for k in COMMON_METRIC_KEYWORDS):
            raise UnsupportedQuestionError(
                f"Question asks about business metrics ('{question}'), but dataset contains no numeric or metric columns."
            )

        # If question is completely domain-mismatched
        # E.g. Employee churn question with pure weather sensor data
        hr_keywords = {"employee", "turnover", "attrition", "hire", "salary", "headcount", "resignation"}
        is_hr_question = bool(q_words.intersection(hr_keywords))
        has_hr_columns = any(
            any(k in c.lower() for k in hr_keywords) for c in available_columns
        )

        if is_hr_question and not has_hr_columns:
            raise UnsupportedQuestionError(
                f"Question asks about human resources ('{question}'), but dataset does not contain HR-related columns."
            )

    def _select_primary_metric(self, question: str, metric_cols: List[str]) -> Optional[str]:
        if not metric_cols:
            return None
        q_lower = question.lower()
        # Look for explicit mention in question
        for col in metric_cols:
            if col.lower() in q_lower:
                return col
        # Look for metric keyword overlap
        for col in metric_cols:
            col_l = col.lower()
            for kw in COMMON_METRIC_KEYWORDS:
                if kw in col_l and kw in q_lower:
                    return col
        return metric_cols[0]

    def _select_primary_dimension(self, question: str, dim_cols: List[str]) -> Optional[str]:
        if not dim_cols:
            return None
        q_lower = question.lower()
        for col in dim_cols:
            if col.lower() in q_lower:
                return col
        for col in dim_cols:
            col_l = col.lower()
            for kw in COMMON_DIMENSION_KEYWORDS:
                if kw in col_l:
                    return col
        return dim_cols[0]

    def _generate_hypotheses(
        self,
        question: str,
        metric: Optional[str],
        dim: Optional[str],
        date_col: Optional[str],
    ) -> List[PlannedHypothesis]:
        hypotheses: List[PlannedHypothesis] = []

        # Hyp 1: Data quality/completeness
        hypotheses.append(
            PlannedHypothesis(
                id="hyp_1",
                statement="Data quality issues, such as missing entries or duplicate records, account for metric anomalies.",
                rationale="Before analyzing business drivers, verify data integrity and volume completeness.",
            )
        )

        # Hyp 2: Dimensional concentration
        if metric and dim:
            hypotheses.append(
                PlannedHypothesis(
                    id="hyp_2",
                    statement=f"The shift in {metric} is concentrated within specific segments of {dim} rather than uniform.",
                    rationale=f"Categorical breakdown of {metric} by {dim} identifies which sub-groups drive variance.",
                )
            )

        # Hyp 3: Temporal trend
        if metric and date_col:
            hypotheses.append(
                PlannedHypothesis(
                    id="hyp_3",
                    statement=f"The variance in {metric} is concentrated in specific time intervals across {date_col}.",
                    rationale=f"Analyzing {metric} over time reveals when the trend initiated and its rate of change.",
                )
            )

        return hypotheses

    def _generate_tasks(
        self,
        all_columns: List[str],
        primary_metric: Optional[str],
        primary_dim: Optional[str],
        primary_date: Optional[str],
        hypotheses: List[PlannedHypothesis],
    ) -> List[PlannedTask]:
        tasks: List[PlannedTask] = []
        hyp_map = {h.id: h for h in hypotheses}

        # Task 1: Dataset Profiling
        tasks.append(
            PlannedTask(
                id="task_1",
                title="Profile dataset structure and distributions",
                description="Compute row counts, column types, missing value percentages, and baseline distributions.",
                task_type="profiling",
                tool_name="dataset_profiler",
                parameters={"columns": all_columns},
                dependency_ids=[],
                hypothesis_id="hyp_1" if "hyp_1" in hyp_map else None,
            )
        )

        # Task 2: Data Validation
        val_params: Dict[str, Any] = {"columns": all_columns}
        if primary_metric:
            val_params["non_negative_columns"] = [primary_metric]

        tasks.append(
            PlannedTask(
                id="task_2",
                title="Validate data quality and integrity constraints",
                description="Scan for missing values, duplicate records, and invalid negative entries in metric columns.",
                task_type="validation",
                tool_name="data_validator",
                parameters=val_params,
                dependency_ids=["task_1"],
                hypothesis_id="hyp_1" if "hyp_1" in hyp_map else None,
            )
        )

        # Task 3: Dimensional Grouped Aggregation
        if primary_metric and primary_dim:
            tasks.append(
                PlannedTask(
                    id="task_3",
                    title=f"Analyze {primary_metric} breakdown by {primary_dim}",
                    description=f"Group data by {primary_dim} and compute sum, mean, and count of {primary_metric}.",
                    task_type="analysis",
                    tool_name="grouped_aggregator",
                    parameters={
                        "group_by": [primary_dim],
                        "metric_column": primary_metric,
                        "agg_funcs": ["sum", "mean", "count"],
                    },
                    dependency_ids=["task_2"],
                    hypothesis_id="hyp_2" if "hyp_2" in hyp_map else None,
                )
            )

        # Task 4: Time-Series Analysis
        if primary_metric and primary_date:
            tasks.append(
                PlannedTask(
                    id="task_4",
                    title=f"Analyze temporal trend of {primary_metric} over {primary_date}",
                    description=f"Aggregate {primary_metric} periodically over {primary_date} and calculate period-over-period changes.",
                    task_type="analysis",
                    tool_name="timeseries_analyzer",
                    parameters={
                        "date_column": primary_date,
                        "metric_column": primary_metric,
                        "frequency": "ME",
                        "agg_func": "sum",
                    },
                    dependency_ids=["task_2"],
                    hypothesis_id="hyp_3" if "hyp_3" in hyp_map else None,
                )
            )

        return tasks


rule_based_planner = RuleBasedPlanner()
