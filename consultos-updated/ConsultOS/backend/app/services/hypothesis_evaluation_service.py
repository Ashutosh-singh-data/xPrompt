import logging
import uuid
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session

from app.models.hypothesis import Hypothesis, HypothesisStatus
from app.models.evidence import Evidence, EvidenceVerificationStatus
from app.models.task import InvestigationTask
from app.models.event import InvestigationEvent
from app.repositories.event_repository import EventRepository

logger = logging.getLogger("consultos.services.hypothesis_evaluation")


class HypothesisEvaluationResult:
    """Evaluation output for a single hypothesis."""

    def __init__(
        self,
        hypothesis_id: str,
        status: HypothesisStatus,
        confidence: Optional[float],
        supporting_evidence: List[Evidence],
        contradictory_evidence: List[Evidence],
        inconclusive_evidence: List[Evidence],
        reasoning: str,
    ):
        self.hypothesis_id = hypothesis_id
        self.status = status
        self.confidence = confidence
        self.supporting_evidence = supporting_evidence
        self.contradictory_evidence = contradictory_evidence
        self.inconclusive_evidence = inconclusive_evidence
        self.reasoning = reasoning


class HypothesisEvaluationService:
    """Evaluates investigation hypotheses against collected, verified evidence.

    Adheres to scientific and statistical integrity:
    - Never invents conclusions.
    - Never claims causation from correlation.
    - Returns inconclusive whenever verified evidence is absent or insufficient.
    - Links supporting and contradictory evidence to hypothesis entities.
    """

    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)

    def evaluate_investigation_hypotheses(
        self,
        investigation_id: str,
    ) -> List[Hypothesis]:
        """Evaluate all hypotheses for an investigation and persist evaluation results."""
        hypotheses = (
            self.db.query(Hypothesis)
            .filter(Hypothesis.investigation_id == investigation_id)
            .order_by(Hypothesis.created_at.asc())
            .all()
        )

        all_evidence = (
            self.db.query(Evidence)
            .filter(Evidence.investigation_id == investigation_id)
            .order_by(Evidence.created_at.asc())
            .all()
        )

        tasks = (
            self.db.query(InvestigationTask)
            .filter(InvestigationTask.investigation_id == investigation_id)
            .all()
        )
        task_map = {t.id: t for t in tasks}

        for hyp in hypotheses:
            eval_res = self.evaluate_single_hypothesis(
                hypothesis=hyp,
                all_evidence=all_evidence,
                task_map=task_map,
            )

            previous_status = hyp.status
            hyp.status = eval_res.status.value
            hyp.confidence = eval_res.confidence

            # Associate relevant evidence in hypothesis_evidence table
            all_relevant = list(
                {e.id: e for e in (eval_res.supporting_evidence + eval_res.contradictory_evidence)}.values()
            )
            hyp.evidence = all_relevant

            # Record hypothesis evaluation audit event
            event = InvestigationEvent(
                id=str(uuid.uuid4()),
                investigation_id=investigation_id,
                event_type="hypothesis_evaluated",
                details={
                    "hypothesis_id": hyp.id,
                    "statement": hyp.statement,
                    "previous_status": previous_status,
                    "status": hyp.status,
                    "confidence": hyp.confidence,
                    "supporting_evidence_count": len(eval_res.supporting_evidence),
                    "contradictory_evidence_count": len(eval_res.contradictory_evidence),
                    "supporting_evidence_ids": [e.id for e in eval_res.supporting_evidence],
                    "contradictory_evidence_ids": [e.id for e in eval_res.contradictory_evidence],
                    "reasoning": eval_res.reasoning,
                },
            )
            self.event_repo.create(event)

        self.db.commit()
        logger.info(
            f"Evaluated {len(hypotheses)} hypotheses for investigation '{investigation_id}'."
        )
        return hypotheses

    def evaluate_single_hypothesis(
        self,
        hypothesis: Hypothesis,
        all_evidence: List[Evidence],
        task_map: Optional[Dict[str, InvestigationTask]] = None,
    ) -> HypothesisEvaluationResult:
        """Evaluate a single hypothesis against collected evidence using domain rules."""
        statement_lower = hypothesis.statement.lower()

        # Categorize evidence into verified vs non-verified
        verified_evidence = [
            e for e in all_evidence if e.verification_status == EvidenceVerificationStatus.VERIFIED.value
        ]

        supporting: List[Evidence] = []
        contradictory: List[Evidence] = []
        inconclusive: List[Evidence] = []

        # 1. Hyp 1 Pattern: Data Quality & Completeness
        if "data quality" in statement_lower or "missing" in statement_lower or "duplicate" in statement_lower:
            val_ev = [e for e in verified_evidence if e.source_type == "validation_tool"]
            if not val_ev:
                # No verified validation evidence
                return HypothesisEvaluationResult(
                    hypothesis_id=hypothesis.id,
                    status=HypothesisStatus.INCONCLUSIVE,
                    confidence=None,
                    supporting_evidence=[],
                    contradictory_evidence=[],
                    inconclusive_evidence=[e for e in all_evidence if e.source_type == "validation_tool"],
                    reasoning="No verified data validation evidence available to evaluate data quality hypothesis.",
                )

            for ev in val_ev:
                sup = ev.supporting_data or {}
                is_valid = sup.get("is_valid", True)
                issues = sup.get("issues", [])
                has_critical_issues = not is_valid or any(
                    isinstance(i, dict) and i.get("severity") == "high" for i in issues
                )

                if has_critical_issues:
                    supporting.append(ev)
                else:
                    contradictory.append(ev)

            if supporting and not contradictory:
                status = HypothesisStatus.SUPPORTED
                confidence = 0.85
                reasoning = (
                    f"Data quality issues verified ({len(supporting)} validation checks detected constraints violations)."
                )
            elif contradictory and not supporting:
                status = HypothesisStatus.CONTRADICTED
                confidence = 0.90
                reasoning = (
                    "Data validation passed with 0 critical issues; anomalies cannot be attributed to data corruption."
                )
            else:
                status = HypothesisStatus.INCONCLUSIVE
                confidence = None
                reasoning = "Conflicting validation outcomes prevent conclusive determination."

            return HypothesisEvaluationResult(
                hypothesis_id=hypothesis.id,
                status=status,
                confidence=confidence,
                supporting_evidence=supporting,
                contradictory_evidence=contradictory,
                inconclusive_evidence=inconclusive,
                reasoning=reasoning,
            )

        # 2. Hyp 2 Pattern: Categorical / Dimensional Concentration
        elif "concentrated within specific segments" in statement_lower or "segment" in statement_lower or "breakdown" in statement_lower:
            agg_ev = [e for e in verified_evidence if e.source_type == "aggregation_tool"]
            if not agg_ev:
                return HypothesisEvaluationResult(
                    hypothesis_id=hypothesis.id,
                    status=HypothesisStatus.INCONCLUSIVE,
                    confidence=None,
                    supporting_evidence=[],
                    contradictory_evidence=[],
                    inconclusive_evidence=[e for e in all_evidence if e.source_type == "aggregation_tool"],
                    reasoning="No verified grouped aggregation evidence available to evaluate dimensional concentration.",
                )

            for ev in agg_ev:
                sup = ev.supporting_data or {}
                total_groups = sup.get("total_groups", 0)
                top_group = sup.get("top_group", {})

                if total_groups <= 1:
                    inconclusive.append(ev)
                elif top_group:
                    supporting.append(ev)
                else:
                    contradictory.append(ev)

            if supporting:
                status = HypothesisStatus.SUPPORTED
                confidence = 0.80
                reasoning = (
                    f"Verified grouped aggregation reveals variance concentrated in top segment."
                )
            elif contradictory:
                status = HypothesisStatus.CONTRADICTED
                confidence = 0.70
                reasoning = "Grouped analysis indicates relatively uniform distribution across segments."
            else:
                status = HypothesisStatus.INCONCLUSIVE
                confidence = None
                reasoning = "Insufficient group variation to establish concentration."

            return HypothesisEvaluationResult(
                hypothesis_id=hypothesis.id,
                status=status,
                confidence=confidence,
                supporting_evidence=supporting,
                contradictory_evidence=contradictory,
                inconclusive_evidence=inconclusive,
                reasoning=reasoning,
            )

        # 3. Hyp 3 Pattern: Temporal Trend
        elif "time intervals" in statement_lower or "temporal" in statement_lower or "over time" in statement_lower:
            ts_ev = [e for e in verified_evidence if e.source_type == "timeseries_tool"]
            if not ts_ev:
                return HypothesisEvaluationResult(
                    hypothesis_id=hypothesis.id,
                    status=HypothesisStatus.INCONCLUSIVE,
                    confidence=None,
                    supporting_evidence=[],
                    contradictory_evidence=[],
                    inconclusive_evidence=[e for e in all_evidence if e.source_type == "timeseries_tool"],
                    reasoning="No verified time-series evidence available to evaluate temporal trend hypothesis.",
                )

            for ev in ts_ev:
                sup = ev.supporting_data or {}
                trend = sup.get("trend_direction", "unknown")
                pct_change = abs(sup.get("overall_change_pct", 0.0))

                if trend in ["increasing", "decreasing", "sharp_rise", "sharp_drop"] and pct_change >= 5.0:
                    supporting.append(ev)
                elif trend == "stable" or pct_change < 2.0:
                    contradictory.append(ev)
                else:
                    inconclusive.append(ev)

            if supporting:
                status = HypothesisStatus.SUPPORTED
                confidence = 0.85
                reasoning = (
                    f"Verified time-series evidence demonstrates temporal trend ({len(supporting)} observations)."
                )
            elif contradictory:
                status = HypothesisStatus.CONTRADICTED
                confidence = 0.75
                reasoning = "Time-series analysis shows flat or negligible variation over time."
            else:
                status = HypothesisStatus.INCONCLUSIVE
                confidence = None
                reasoning = "Time-series trend was weak, inconclusive, or lacked sufficient historical periods."

            return HypothesisEvaluationResult(
                hypothesis_id=hypothesis.id,
                status=status,
                confidence=confidence,
                supporting_evidence=supporting,
                contradictory_evidence=contradictory,
                inconclusive_evidence=inconclusive,
                reasoning=reasoning,
            )

        # 4. Default / Generic Hypotheses
        else:
            if not verified_evidence:
                return HypothesisEvaluationResult(
                    hypothesis_id=hypothesis.id,
                    status=HypothesisStatus.INCONCLUSIVE,
                    confidence=None,
                    supporting_evidence=[],
                    contradictory_evidence=[],
                    inconclusive_evidence=all_evidence,
                    reasoning="No verified evidence available to evaluate generic hypothesis.",
                )

            # Heuristic match by wording
            for ev in verified_evidence:
                f_words = set(ev.finding.lower().split())
                h_words = set(statement_lower.split())
                overlap = f_words.intersection(h_words)
                if len(overlap) >= 3:
                    supporting.append(ev)

            if supporting:
                status = HypothesisStatus.SUPPORTED
                confidence = min(0.85, 0.5 + 0.1 * len(supporting))
                reasoning = f"Supported by {len(supporting)} verified evidence findings."
            else:
                status = HypothesisStatus.INCONCLUSIVE
                confidence = None
                reasoning = "No verified findings directly support or contradict the hypothesis."

            return HypothesisEvaluationResult(
                hypothesis_id=hypothesis.id,
                status=status,
                confidence=confidence,
                supporting_evidence=supporting,
                contradictory_evidence=[],
                inconclusive_evidence=[],
                reasoning=reasoning,
            )
