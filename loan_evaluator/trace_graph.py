"""LangSmith/LangGraph trace shaping for loan evaluations."""

from __future__ import annotations

import json
from typing import Any, Dict, List, TypedDict

try:
    from .models import EvaluationResult, LoanApplication, ReviewResult
except ImportError:
    from models import EvaluationResult, LoanApplication, ReviewResult


def application_trace_summary(application: LoanApplication) -> Dict[str, Any]:
    """Create a redacted application summary for LangSmith."""
    return {
        "loan_purpose": application.loan_purpose,
        "loan_term_months": application.loan_term_months,
        "employment_status": application.employment_status,
        "documents_count": len(application.documents_provided),
        "has_collateral": application.collateral_value is not None,
        "has_secondary_income": bool(application.secondary_income),
        "has_bankruptcy_history": bool(application.bankruptcy_history),
    }


def review_trace_summary(review: ReviewResult) -> Dict[str, Any]:
    """Create a redacted review summary for LangSmith."""
    return {
        "reviewer_name": review.reviewer_name,
        "score": review.score,
        "recommended_action": review.recommended_action,
        "confidence": review.confidence,
        "fraud_risk_level": review.fraud_risk_level,
        "documentation_status": review.documentation_status,
    }


def evaluation_trace_summary(evaluation: EvaluationResult) -> Dict[str, Any]:
    """Create a redacted top-level evaluation output for LangSmith."""
    return {
        "final_recommendation": evaluation.final_recommendation,
        "overall_score": evaluation.overall_score,
        "avg_confidence": evaluation.avg_confidence,
        "agents_involved": evaluation.agents_involved,
        "review_count": len(evaluation.reviews),
        "reviews": [
            review_trace_summary(review)
            for review in evaluation.reviews
        ],
    }


def rationale_trace_summary(reviews: List[ReviewResult]) -> Dict[str, Any]:
    """Create a redacted summary of the reasoning signals across agents."""
    final_review = reviews[-1] if reviews else None
    rationale = final_review.overall_rationale if final_review else None

    action_counts: Dict[str, int] = {}
    for review in reviews:
        action_counts[review.recommended_action] = (
            action_counts.get(review.recommended_action, 0) + 1
        )

    scores = [review.score for review in reviews]
    confidences = [review.confidence for review in reviews]

    return {
        "source": (
            "loan_officer_overall_rationale"
            if rationale
            else "aggregated_agent_reasoning_signals"
        ),
        "rationale_present": bool(rationale),
        "rationale_length": len(rationale or ""),
        "rationale_redacted": True,
        "agent_count": len(reviews),
        "actions": action_counts,
        "score_min": min(scores) if scores else None,
        "score_max": max(scores) if scores else None,
        "score_avg": sum(scores) / len(scores) if scores else None,
        "confidence_avg": (
            sum(confidences) / len(confidences)
            if confidences
            else None
        ),
        "review_signals": [
            {
                "reviewer_name": review.reviewer_name,
                "score": review.score,
                "recommended_action": review.recommended_action,
                "confidence": review.confidence,
                "strength_count": len(review.strengths),
                "weakness_count": len(review.weaknesses),
                "risk_count": len(review.risks),
                "condition_count": len(review.conditions_for_approval or []),
                "required_document_count": len(review.required_documents or []),
                "has_overall_rationale": bool(review.overall_rationale),
            }
            for review in reviews
        ],
    }


def agent_output_trace_payload(output: object) -> Dict[str, Any]:
    """Create a redacted agent output payload for LangSmith."""
    raw_output = str(output)
    payload: Dict[str, Any] = {
        "raw_output_redacted": True,
    }

    try:
        json_str = raw_output
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        parsed = json.loads(json_str)
        if isinstance(parsed, dict):
            normalized = _normalize_review_json(
                parsed,
                str(parsed.get("reviewer_name", "unknown")),
            )
            payload["summary"] = {
                key: normalized.get(key)
                for key in (
                    "reviewer_name",
                    "score",
                    "recommended_action",
                    "confidence",
                    "fraud_risk_level",
                    "documentation_status",
                )
                if normalized.get(key) is not None
            }
            payload["parse_status"] = "parsed"
    except (json.JSONDecodeError, ValueError):
        payload["parse_status"] = "raw_output_not_json"

    return payload


async def run_langsmith_trace_graph(evaluator: Any, application: LoanApplication) -> EvaluationResult:
    """Run evaluation through LangGraph so LangSmith shows clear graph nodes."""
    try:
        from langgraph.graph import END, START, StateGraph
        from langsmith import tracing_context
    except ImportError as e:
        raise RuntimeError(
            "LangGraph is required for LangSmith graph traces. "
            "Install dependencies with: pip install -r requirements.txt"
        ) from e

    class TraceState(TypedDict, total=False):
        application: Dict[str, Any]
        reviews: List[Dict[str, Any]]
        rationale: Dict[str, Any]
        evaluation: Dict[str, Any]

    app_text_holder: Dict[str, str] = {}
    reviews: List[ReviewResult] = []
    final_review_holder: Dict[str, ReviewResult] = {}
    evaluation_holder: Dict[str, EvaluationResult] = {}

    async def format_application_node(state: TraceState) -> TraceState:
        app_text_holder["text"] = evaluator._format_application_for_review(application)
        return {
            "application": application_trace_summary(application),
            "reviews": [],
        }

    async def credit_analyst_node(state: TraceState) -> TraceState:
        print("Running Credit Risk Analysis...")
        review = await evaluator._get_agent_review(
            evaluator.evaluators["credit_analyst"],
            app_text_holder["text"],
            "credit_risk_analyst",
        )
        reviews.append(review)
        return {"reviews": [review_trace_summary(r) for r in reviews]}

    async def compliance_officer_node(state: TraceState) -> TraceState:
        print("Running Compliance Review...")
        review = await evaluator._get_agent_review(
            evaluator.evaluators["compliance_officer"],
            app_text_holder["text"],
            "compliance_officer",
        )
        reviews.append(review)
        return {"reviews": [review_trace_summary(r) for r in reviews]}

    async def fraud_detector_node(state: TraceState) -> TraceState:
        print("Running Fraud Detection...")
        review = await evaluator._get_agent_review(
            evaluator.evaluators["fraud_detector"],
            app_text_holder["text"],
            "fraud_detection_specialist",
        )
        reviews.append(review)
        return {"reviews": [review_trace_summary(r) for r in reviews]}

    async def loan_officer_node(state: TraceState) -> TraceState:
        synthesis_prompt = evaluator._create_synthesis_prompt(application, reviews)
        print("Getting Final Loan Officer Review...")
        final_review = await evaluator._get_agent_review(
            evaluator.evaluators["loan_officer"],
            synthesis_prompt,
            "loan_officer",
        )
        final_review_holder["review"] = final_review
        reviews.append(final_review)
        return {"reviews": [review_trace_summary(r) for r in reviews]}

    async def decision_rationale_node(state: TraceState) -> TraceState:
        return {"rationale": rationale_trace_summary(reviews)}

    async def aggregate_decision_node(state: TraceState) -> TraceState:
        evaluation = evaluator._synthesize_results(
            application,
            reviews,
            final_review_holder["review"],
        )
        evaluation_holder["result"] = evaluation
        return {"evaluation": evaluation_trace_summary(evaluation)}

    workflow = StateGraph(TraceState)
    workflow.add_node("format_application", format_application_node)
    workflow.add_node("credit_risk_analyst", credit_analyst_node)
    workflow.add_node("compliance_officer", compliance_officer_node)
    workflow.add_node("fraud_detection_specialist", fraud_detector_node)
    workflow.add_node("loan_officer", loan_officer_node)
    workflow.add_node("decision_rationale", decision_rationale_node)
    workflow.add_node("aggregate_decision", aggregate_decision_node)

    workflow.add_edge(START, "format_application")
    workflow.add_edge("format_application", "credit_risk_analyst")
    workflow.add_edge("credit_risk_analyst", "compliance_officer")
    workflow.add_edge("compliance_officer", "fraud_detection_specialist")
    workflow.add_edge("fraud_detection_specialist", "loan_officer")
    workflow.add_edge("loan_officer", "decision_rationale")
    workflow.add_edge("decision_rationale", "aggregate_decision")
    workflow.add_edge("aggregate_decision", END)

    graph = workflow.compile()
    initial_state: TraceState = {
        "application": application_trace_summary(application),
        "reviews": [],
        "rationale": {},
    }

    with tracing_context(
        enabled=True,
        project_name=evaluator.langsmith_project,
        client=evaluator.langsmith_client,
    ):
        await graph.ainvoke(
            initial_state,
            config={
                "run_name": "loan-evaluation",
                "metadata": {
                    "ls_provider": "aws-bedrock",
                    "ls_model_name": evaluator.model.config.get("model_id"),
                },
            },
        )

    evaluator._flush_langsmith()
    return evaluation_holder["result"]


def _normalize_review_json(
    json_data: Dict[str, Any], reviewer_type: str
) -> Dict[str, Any]:
    """Normalize common LLM response variants into ReviewResult fields."""
    normalized = dict(json_data)

    if "recommended_action" not in normalized:
        for alias in ("final_recommendation", "recommendation", "action"):
            if alias in normalized:
                normalized["recommended_action"] = normalized[alias]
                break

    if reviewer_type == "loan_officer":
        normalized["reviewer_name"] = "loan_officer"

    return normalized
