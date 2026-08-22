"""Peptide quality assessment protocol — domain-specific reasoning for Peptide Checker.

This module bridges HUMMBL's structured reasoning framework to the peptide
quality domain. Every assessment generates an auditable ReasoningTrace with
five steps: OBSERVE -> EVALUATE -> HYPOTHESIZE -> DECIDE -> REFLECT.

The reasoning is explicit: instead of a black-box grade, the trace shows
exactly what data was seen, what thresholds were applied, what hypotheses
were considered, and why the final grade was assigned.

Usage:
    from hummbl.peptide_protocol import PeptideQualityProtocol

    protocol = PeptideQualityProtocol()
    trace = protocol.evaluate_test_result(test_data)
    print(trace.to_json())
"""

from __future__ import annotations

import json
from typing import Optional

from hummbl.protocols import ReasoningProtocol, StepSpec
from hummbl.reasoning import (
    ReasoningTopology,
    ReasoningTrace,
    StepType,
    make_step,
)
from hummbl.peptide_rules import (
    GRADE_RECOMMENDATIONS,
    PEPTIDE_SPECS,
    VENDOR_TRUST_TIERS,
    PeptideSpec,
    assess_contaminants,
    assess_purity,
    get_spec,
    score_to_grade,
)


class PeptideQualityProtocol(ReasoningProtocol):
    """Structured reasoning for evaluating peptide quality.

    Step sequence: OBSERVE -> EVALUATE -> HYPOTHESIZE -> DECIDE -> REFLECT

    This protocol extends the QualityAssessment stub in protocols.py with
    real peptide domain logic: purity thresholds, degradation analysis,
    vendor trust scoring, and consumer-facing recommendations.
    """

    def __init__(self) -> None:
        super().__init__(
            name="peptide_quality",
            description=(
                "Five-step structured reasoning for peptide quality assessment. "
                "Observe data, evaluate against standards, hypothesize causes, "
                "decide on grade, reflect on vendor patterns."
            ),
            domain="peptide_qa",
            topology=ReasoningTopology.CHAIN,
            step_specs=[
                StepSpec(
                    type=StepType.OBSERVATION,
                    name="observe_data",
                    description=(
                        "Parse the raw test result: purity %, identity "
                        "confirmation, contaminants, Finnrick scores."
                    ),
                    metadata_keys=[
                        "peptide_name", "vendor", "purity_percent",
                        "identity_confirmed", "grade_source",
                    ],
                ),
                StepSpec(
                    type=StepType.EVALUATION,
                    name="evaluate_standards",
                    description=(
                        "Compare each measurement to peptide-specific "
                        "thresholds. Flag pass / warning / fail."
                    ),
                    metadata_keys=[
                        "purity_status", "contaminant_status",
                        "identity_status", "overall_status",
                    ],
                ),
                StepSpec(
                    type=StepType.HYPOTHESIS,
                    name="hypothesize_causes",
                    description=(
                        "If any issues found, hypothesize root cause: "
                        "degradation, synthesis error, adulteration, etc."
                    ),
                    required=False,
                ),
                StepSpec(
                    type=StepType.DECISION,
                    name="assign_grade",
                    description=(
                        "Assign a letter grade (A-E/U) and a consumer-facing "
                        "recommendation."
                    ),
                    metadata_keys=["grade", "recommendation", "confidence"],
                ),
                StepSpec(
                    type=StepType.REFLECTION,
                    name="vendor_reflection",
                    description=(
                        "Reflect on vendor history and update trust assessment."
                    ),
                    metadata_keys=["vendor_trust_tier", "notes"],
                    required=False,
                ),
            ],
        )

    # -----------------------------------------------------------------
    # Primary assessment entry point
    # -----------------------------------------------------------------

    def evaluate_test_result(self, test_data: dict) -> ReasoningTrace:
        """Generate a full reasoning trace for a single peptide test result.

        Args:
            test_data: A dict conforming to the peptide-checker schema.json
                       format (peptide_name, vendor, purity_percent, grade, etc.)

        Returns:
            A complete ReasoningTrace with all steps populated.
        """
        trace = self.create_trace(
            tags=["peptide_qa", test_data.get("peptide_name", "unknown")]
        )

        peptide_name = test_data.get("peptide_name", "unknown")
        vendor = test_data.get("vendor", "unknown")
        spec = get_spec(peptide_name)

        # ---- Step 1: OBSERVATION ----
        obs_step = self._step_observe(test_data, spec)
        trace.add_step(obs_step)

        # ---- Step 2: EVALUATION ----
        eval_step = self._step_evaluate(test_data, spec, parent_id=obs_step.id)
        trace.add_step(eval_step)

        # ---- Step 3: HYPOTHESIS (only if issues found) ----
        hyp_step = self._step_hypothesize(
            test_data, spec, eval_step, parent_id=eval_step.id
        )
        if hyp_step is not None:
            trace.add_step(hyp_step)
            decision_parent = hyp_step.id
        else:
            decision_parent = eval_step.id

        # ---- Step 4: DECISION ----
        dec_step = self._step_decide(
            test_data, spec, eval_step, parent_id=decision_parent
        )
        trace.add_step(dec_step)

        # ---- Step 5: REFLECTION ----
        ref_step = self._step_reflect(
            test_data, spec, dec_step, parent_id=dec_step.id
        )
        trace.add_step(ref_step)

        # Set trace outcome
        trace.outcome = dec_step.metadata.get("grade", "U")
        return trace

    # -----------------------------------------------------------------
    # Vendor comparison
    # -----------------------------------------------------------------

    def compare_vendors(self, vendor_data: list[dict]) -> ReasoningTrace:
        """Generate a reasoning trace comparing multiple vendors for a peptide.

        Args:
            vendor_data: List of test result dicts, each for a different vendor
                         of the same peptide.

        Returns:
            A ReasoningTrace with observation (summary of all vendors),
            evaluation (ranked comparison), and decision (recommended vendor).
        """
        if not vendor_data:
            trace = self.create_trace(tags=["peptide_qa", "vendor_comparison"])
            step = make_step(
                StepType.OBSERVATION,
                "No vendor data provided for comparison.",
            )
            trace.add_step(step)
            trace.outcome = "no_data"
            return trace

        peptide_name = vendor_data[0].get("peptide_name", "unknown")
        trace = self.create_trace(
            tags=["peptide_qa", "vendor_comparison", peptide_name]
        )

        # Observation: summarize all vendors
        summaries = []
        for vd in vendor_data:
            v = vd.get("vendor", "?")
            g = vd.get("grade", "U")
            s = vd.get("score_avg")
            tc = vd.get("test_count")
            score_str = f"{s:.1f}" if s is not None else "N/A"
            tc_str = str(tc) if tc is not None else "N/A"
            summaries.append(f"  {v}: grade={g}, score={score_str}, tests={tc_str}")

        obs_step = make_step(
            StepType.OBSERVATION,
            f"Comparing {len(vendor_data)} vendors for {peptide_name}:\n"
            + "\n".join(summaries),
            metadata={
                "peptide_name": peptide_name,
                "vendor_count": len(vendor_data),
            },
        )
        trace.add_step(obs_step)

        # Evaluation: rank by grade then score
        grade_order = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "U": 5}
        ranked = sorted(
            vendor_data,
            key=lambda d: (
                grade_order.get(d.get("grade", "U"), 5),
                -(d.get("score_avg") or 0),
            ),
        )

        ranking_lines = []
        for i, vd in enumerate(ranked, 1):
            v = vd.get("vendor", "?")
            g = vd.get("grade", "U")
            s = vd.get("score_avg")
            tent = " (tentative)" if vd.get("tentative") else ""
            score_str = f"{s:.1f}" if s is not None else "N/A"
            ranking_lines.append(f"  #{i} {v} — grade {g}, score {score_str}{tent}")

        eval_step = make_step(
            StepType.EVALUATION,
            f"Ranked vendors for {peptide_name}:\n" + "\n".join(ranking_lines),
            parent_id=obs_step.id,
            metadata={
                "top_vendor": ranked[0].get("vendor", "?"),
                "top_grade": ranked[0].get("grade", "U"),
                "bottom_vendor": ranked[-1].get("vendor", "?"),
                "bottom_grade": ranked[-1].get("grade", "U"),
            },
        )
        trace.add_step(eval_step)

        # Decision: recommend top vendor(s)
        top_grade = ranked[0].get("grade", "U")
        top_vendors = [
            vd.get("vendor", "?")
            for vd in ranked
            if vd.get("grade") == top_grade
        ]
        rec = GRADE_RECOMMENDATIONS.get(top_grade, "Unknown grade.")
        non_tentative_top = [
            vd.get("vendor", "?")
            for vd in ranked
            if vd.get("grade") == top_grade and not vd.get("tentative")
        ]

        if non_tentative_top:
            recommend_str = (
                f"Recommended vendor(s): {', '.join(non_tentative_top)} "
                f"(grade {top_grade}). {rec}"
            )
        elif top_vendors:
            recommend_str = (
                f"Top vendor(s): {', '.join(top_vendors)} "
                f"(grade {top_grade}, tentative). {rec} "
                f"Note: ratings are tentative due to limited test data."
            )
        else:
            recommend_str = "No vendors available for recommendation."

        dec_step = make_step(
            StepType.DECISION,
            recommend_str,
            parent_id=eval_step.id,
            metadata={
                "recommended_vendors": non_tentative_top or top_vendors,
                "grade": top_grade,
                "recommendation": rec,
            },
        )
        trace.add_step(dec_step)
        trace.outcome = top_grade
        return trace

    # -----------------------------------------------------------------
    # Degradation risk assessment
    # -----------------------------------------------------------------

    def assess_degradation_risk(
        self,
        peptide: str,
        storage_conditions: dict,
    ) -> ReasoningTrace:
        """Reasoning about degradation risk given storage conditions.

        Args:
            peptide: Peptide name (e.g. "BPC-157").
            storage_conditions: Dict with keys like 'temp_c',
                'days_since_reconstitution', 'light_exposure', etc.

        Returns:
            A ReasoningTrace assessing degradation risk.
        """
        trace = self.create_trace(
            tags=["peptide_qa", "degradation_risk", peptide]
        )
        spec = get_spec(peptide)

        temp_c = storage_conditions.get("temp_c")
        days = storage_conditions.get("days_since_reconstitution", 0)
        light = storage_conditions.get("light_exposure", False)
        is_reconstituted = storage_conditions.get("reconstituted", False)

        # Observation
        condition_lines = [f"  Temperature: {temp_c} C" if temp_c is not None else "  Temperature: unknown"]
        condition_lines.append(f"  Reconstituted: {'yes' if is_reconstituted else 'no'}")
        if is_reconstituted:
            condition_lines.append(f"  Days since reconstitution: {days}")
        condition_lines.append(f"  Light exposure: {'yes' if light else 'no'}")

        obs = make_step(
            StepType.OBSERVATION,
            f"Storage conditions for {peptide}:\n" + "\n".join(condition_lines),
            metadata=storage_conditions,
        )
        trace.add_step(obs)

        # Evaluation: check each risk factor
        risks: list[str] = []
        risk_level = "low"

        if spec is None:
            risks.append(f"No spec data for '{peptide}'; cannot assess thresholds.")
            risk_level = "unknown"
        else:
            # Temperature
            if temp_c is not None:
                if spec.never_freeze and temp_c < 0:
                    risks.append(
                        f"FREEZE DAMAGE: {peptide} must not be frozen "
                        f"(current: {temp_c} C). Aggregation and loss of "
                        f"bioactivity likely."
                    )
                    risk_level = "high"
                elif temp_c > spec.storage_temp_max_c:
                    delta = temp_c - spec.storage_temp_max_c
                    risks.append(
                        f"Temperature {temp_c} C exceeds max "
                        f"{spec.storage_temp_max_c} C by {delta:.0f} C. "
                        f"Accelerated degradation expected."
                    )
                    risk_level = "high" if delta > 20 else "moderate"

            # Reconstituted shelf life
            if is_reconstituted and spec and days > spec.reconstituted_shelf_days:
                risks.append(
                    f"Reconstituted {days} days ago, exceeding shelf life of "
                    f"{spec.reconstituted_shelf_days} days. Degradation likely."
                )
                risk_level = "high"

            # Light
            if light:
                risks.append(
                    "Light exposure detected. Peptides are photosensitive; "
                    "oxidation products may form."
                )
                if risk_level == "low":
                    risk_level = "moderate"

            # Known degradation products
            if spec and spec.known_degradation:
                deg_str = ", ".join(spec.known_degradation)
                risks.append(
                    f"Known degradation pathways for {peptide}: {deg_str}."
                )

        if not risks:
            risks.append("No risk factors identified. Storage appears adequate.")

        eval_step = make_step(
            StepType.EVALUATION,
            f"Degradation risk assessment for {peptide}:\n"
            + "\n".join(f"  - {r}" for r in risks),
            parent_id=obs.id,
            metadata={"risk_level": risk_level, "risk_count": len(risks)},
        )
        trace.add_step(eval_step)

        # Decision
        if risk_level == "high":
            rec = f"Do not use. {peptide} has likely degraded under these conditions."
        elif risk_level == "moderate":
            rec = f"Use with caution. Request fresh sample or re-test for {peptide}."
        elif risk_level == "unknown":
            rec = f"Cannot assess — no reference data for {peptide}."
        else:
            rec = f"Storage conditions are within acceptable range for {peptide}."

        dec_step = make_step(
            StepType.DECISION,
            rec,
            parent_id=eval_step.id,
            metadata={"risk_level": risk_level, "recommendation": rec},
        )
        trace.add_step(dec_step)
        trace.outcome = risk_level
        return trace

    # =================================================================
    # Private step builders
    # =================================================================

    def _step_observe(
        self,
        data: dict,
        spec: Optional[PeptideSpec],
    ) -> "ReasoningStep":
        """Step 1 — OBSERVATION: What does the data show?"""
        peptide = data.get("peptide_name", "unknown")
        vendor = data.get("vendor", "unknown")
        purity = data.get("purity_percent")
        identity = data.get("identity_confirmed")
        degradation = data.get("degradation_products")
        contaminants = data.get("contaminants")
        endotoxin = data.get("endotoxin_eu_per_mg")
        heavy_metals = data.get("heavy_metals_ppm")
        grade_given = data.get("grade")
        score_avg = data.get("score_avg")
        test_count = data.get("test_count")
        source = data.get("source", "unknown")

        lines = [
            f"Peptide: {peptide}",
            f"Vendor: {vendor}",
            f"Source: {source}",
        ]
        if purity is not None:
            lines.append(f"Purity: {purity:.1f}%")
        else:
            lines.append("Purity: not reported")

        if identity is not None:
            lines.append(f"Identity confirmed: {'yes' if identity else 'NO'}")
        else:
            lines.append("Identity confirmation: not reported")

        if degradation:
            lines.append(f"Degradation products: {', '.join(degradation)}")
        if contaminants:
            lines.append(f"Contaminants: {json.dumps(contaminants)}")
        if endotoxin is not None:
            lines.append(f"Endotoxin: {endotoxin:.2f} EU/mg")
        if heavy_metals is not None:
            lines.append(f"Heavy metals: {heavy_metals:.1f} ppm")
        if grade_given:
            lines.append(f"Source grade: {grade_given}")
        if score_avg is not None:
            lines.append(f"Finnrick avg score: {score_avg:.1f}")
        if test_count is not None:
            lines.append(f"Test count: {test_count}")
        if data.get("tentative"):
            lines.append("Rating is TENTATIVE (fewer than 5 samples)")
        if data.get("notes"):
            lines.append(f"Notes: {data['notes']}")

        return make_step(
            StepType.OBSERVATION,
            "Test data ingested:\n  " + "\n  ".join(lines),
            metadata={
                "peptide_name": peptide,
                "vendor": vendor,
                "purity_percent": purity,
                "identity_confirmed": identity,
                "grade_source": grade_given,
                "score_avg": score_avg,
                "test_count": test_count,
                "source": source,
            },
        )

    def _step_evaluate(
        self,
        data: dict,
        spec: Optional[PeptideSpec],
        parent_id: str,
    ) -> "ReasoningStep":
        """Step 2 — EVALUATION: How does this compare to standards?"""
        findings: list[str] = []
        overall_status = "pass"
        purity_status = "unknown"
        contaminant_status = "pass"
        identity_status = "unknown"

        peptide = data.get("peptide_name", "unknown")

        # Purity
        purity = data.get("purity_percent")
        if spec and purity is not None:
            status, explanation = assess_purity(purity, spec)
            purity_status = status
            findings.append(f"Purity: {explanation}")
            if status == "fail":
                overall_status = "fail"
            elif status == "warning" and overall_status != "fail":
                overall_status = "warning"
        elif purity is None:
            findings.append(
                "Purity not reported. Evaluating based on Finnrick scores."
            )
            # Fall back to Finnrick score-based assessment
            score_avg = data.get("score_avg")
            if score_avg is not None:
                derived_grade = score_to_grade(score_avg, data.get("test_count"))
                findings.append(
                    f"Finnrick score {score_avg:.1f} maps to derived grade: {derived_grade}."
                )
                purity_status = "inferred"
                if derived_grade in ("D", "E"):
                    overall_status = "fail"
                elif derived_grade == "C" and overall_status != "fail":
                    overall_status = "warning"

        # Identity
        identity = data.get("identity_confirmed")
        if identity is True:
            identity_status = "pass"
            findings.append("Identity confirmed via mass spectrometry or equivalent.")
        elif identity is False:
            identity_status = "fail"
            overall_status = "fail"
            findings.append("IDENTITY NOT CONFIRMED — wrong peptide or degraded.")
        else:
            findings.append("Identity confirmation not reported.")

        # Contaminants
        if spec:
            contam_results = assess_contaminants(
                data.get("endotoxin_eu_per_mg"),
                data.get("heavy_metals_ppm"),
                spec,
            )
            for status, explanation in contam_results:
                findings.append(explanation)
                if status == "fail":
                    contaminant_status = "fail"
                    overall_status = "fail"

        # Degradation products
        degradation = data.get("degradation_products")
        if degradation and spec:
            known = set(d.lower() for d in spec.known_degradation)
            unexpected = [d for d in degradation if d.lower() not in known]
            if unexpected:
                findings.append(
                    f"Unexpected degradation products: {', '.join(unexpected)}. "
                    f"Possible contamination or non-standard synthesis."
                )
                if overall_status != "fail":
                    overall_status = "warning"
            else:
                findings.append(
                    f"Degradation products detected ({', '.join(degradation)}) "
                    f"are known pathways for {peptide}."
                )

        # Source grade consistency check
        grade_given = data.get("grade")
        score_avg = data.get("score_avg")
        if grade_given and score_avg is not None:
            derived = score_to_grade(score_avg, data.get("test_count"))
            if derived != grade_given:
                findings.append(
                    f"Note: Source grade ({grade_given}) differs from "
                    f"score-derived grade ({derived}). Source grade may "
                    f"incorporate factors beyond score average."
                )

        return make_step(
            StepType.EVALUATION,
            "Evaluation against standards:\n  " + "\n  ".join(findings),
            parent_id=parent_id,
            metadata={
                "purity_status": purity_status,
                "contaminant_status": contaminant_status,
                "identity_status": identity_status,
                "overall_status": overall_status,
                "standard_name": f"{peptide} quality thresholds" if spec else "none",
                "pass_fail": overall_status,
            },
        )

    def _step_hypothesize(
        self,
        data: dict,
        spec: Optional[PeptideSpec],
        eval_step: "ReasoningStep",
        parent_id: str,
    ) -> Optional["ReasoningStep"]:
        """Step 3 — HYPOTHESIS: What might explain the results?

        Only generated when issues are found (overall_status != 'pass').
        """
        overall = eval_step.metadata.get("overall_status", "pass")
        if overall == "pass":
            return None

        peptide = data.get("peptide_name", "unknown")
        purity = data.get("purity_percent")
        identity = data.get("identity_confirmed")
        degradation = data.get("degradation_products")
        score_avg = data.get("score_avg")
        grade = data.get("grade")

        hypotheses: list[str] = []

        # Low purity hypotheses
        if purity is not None and spec and purity < spec.min_purity:
            hypotheses.append(
                f"Synthesis quality issue: Purity {purity:.1f}% suggests "
                f"incomplete coupling or inadequate purification."
            )
            hypotheses.append(
                f"Degradation in transit/storage: Product may have been "
                f"exposed to heat or moisture during shipping."
            )
            if purity < spec.warning_purity:
                hypotheses.append(
                    "Possible intentional adulteration or substitution — "
                    "purity significantly below acceptable range."
                )

        # Identity mismatch
        if identity is False:
            hypotheses.append(
                "Wrong peptide: Vendor may have shipped incorrect product."
            )
            hypotheses.append(
                f"Truncated sequence: Incomplete synthesis of {peptide} "
                f"producing a fragment with different mass."
            )
            hypotheses.append(
                "Isomer or analog: Mass spec may have detected a structural "
                "isomer rather than the target sequence."
            )

        # Poor Finnrick score with no analytical data
        if purity is None and score_avg is not None and grade in ("D", "E"):
            hypotheses.append(
                f"Community testing indicates consistent quality issues "
                f"(score {score_avg:.1f}, grade {grade}). Without analytical "
                f"data, specific cause cannot be determined."
            )
            hypotheses.append(
                "Vendor may lack proper synthesis/QC infrastructure, "
                "leading to batch-to-batch variability."
            )

        # Known degradation
        if degradation and spec:
            hypotheses.append(
                f"Detected degradation ({', '.join(degradation)}) consistent "
                f"with known pathways for {peptide}. Likely due to improper "
                f"storage conditions (temp > {spec.storage_temp_max_c} C) "
                f"or age of product."
            )

        if not hypotheses:
            hypotheses.append(
                "Minor issues detected but no specific root cause can be "
                "determined from available data."
            )

        return make_step(
            StepType.HYPOTHESIS,
            "Possible explanations:\n  " + "\n  ".join(
                f"H{i}: {h}" for i, h in enumerate(hypotheses, 1)
            ),
            parent_id=parent_id,
            metadata={
                "hypothesis_count": len(hypotheses),
                "overall_status": overall,
            },
            confidence=0.6 if purity is None else 0.8,
        )

    def _step_decide(
        self,
        data: dict,
        spec: Optional[PeptideSpec],
        eval_step: "ReasoningStep",
        parent_id: str,
    ) -> "ReasoningStep":
        """Step 4 — DECISION: Grade and recommendation."""
        overall = eval_step.metadata.get("overall_status", "pass")
        grade_given = data.get("grade")
        score_avg = data.get("score_avg")
        test_count = data.get("test_count")
        purity = data.get("purity_percent")

        # Determine final grade
        # Priority: analytical data > source grade > score-derived grade
        if purity is not None and spec:
            if overall == "fail":
                final_grade = "D" if purity >= spec.warning_purity else "E"
            elif overall == "warning":
                final_grade = "C"
            else:
                final_grade = "A" if purity >= spec.min_purity else "B"
        elif grade_given:
            # Trust source grade when no analytical data
            final_grade = grade_given
        else:
            final_grade = score_to_grade(score_avg, test_count)

        recommendation = GRADE_RECOMMENDATIONS.get(final_grade, "Unknown.")
        tentative = data.get("tentative", False)
        if tentative:
            recommendation += " (Tentative — limited test data.)"

        # Confidence based on data completeness
        data_points = sum([
            purity is not None,
            data.get("identity_confirmed") is not None,
            data.get("endotoxin_eu_per_mg") is not None,
            data.get("heavy_metals_ppm") is not None,
            score_avg is not None,
            (test_count or 0) >= 5,
        ])
        confidence = min(1.0, 0.3 + data_points * 0.12)

        justification_parts = [f"Final grade: {final_grade}."]
        if purity is not None:
            justification_parts.append(f"Based on measured purity {purity:.1f}%.")
        elif grade_given:
            justification_parts.append(f"Based on source grade from {data.get('source', 'database')}.")
        if tentative:
            justification_parts.append("Rating is tentative.")
        justification_parts.append(f"Recommendation: {recommendation}")

        return make_step(
            StepType.DECISION,
            " ".join(justification_parts),
            parent_id=parent_id,
            metadata={
                "grade": final_grade,
                "recommendation": recommendation,
                "confidence": round(confidence, 2),
                "data_completeness": f"{data_points}/6",
            },
            confidence=confidence,
        )

    def _step_reflect(
        self,
        data: dict,
        spec: Optional[PeptideSpec],
        dec_step: "ReasoningStep",
        parent_id: str,
    ) -> "ReasoningStep":
        """Step 5 — REFLECTION: Vendor patterns and learnings."""
        vendor = data.get("vendor", "unknown")
        grade = dec_step.metadata.get("grade", "U")
        score_avg = data.get("score_avg")
        test_count = data.get("test_count", 0) or 0

        # Determine vendor trust tier
        trust_tier = "U"
        for tier_grade in ("A", "B", "C", "D", "E"):
            tier = VENDOR_TRUST_TIERS[tier_grade]
            if grade <= tier_grade and (score_avg or 0) >= tier.min_avg_score:
                trust_tier = tier_grade
                break
        else:
            trust_tier = grade  # fall through to same as product grade

        tier_info = VENDOR_TRUST_TIERS.get(trust_tier)
        tier_label = tier_info.label if tier_info else "Unknown"

        notes: list[str] = []

        # Reflect on test count
        if test_count >= 10:
            notes.append(
                f"Vendor has {test_count} tests — robust data for assessment."
            )
        elif test_count >= 5:
            notes.append(
                f"Vendor has {test_count} tests — moderate confidence."
            )
        elif test_count > 0:
            notes.append(
                f"Vendor has only {test_count} tests — rating may shift "
                f"as more data accumulates."
            )
        else:
            notes.append("No test count data — assessment is speculative.")

        # Check for vendor-specific notes
        if data.get("notes"):
            notes.append(f"Database note: {data['notes']}")

        # Actionable reflection
        if grade in ("A", "B"):
            notes.append(
                f"Vendor '{vendor}' is performing well. Continue monitoring."
            )
        elif grade == "C":
            notes.append(
                f"Vendor '{vendor}' shows variability. Consider requesting "
                f"batch-specific CoA before purchase."
            )
        else:
            notes.append(
                f"Vendor '{vendor}' has significant quality concerns. "
                f"Recommend avoiding and reporting to community database."
            )

        return make_step(
            StepType.REFLECTION,
            f"Vendor reflection for '{vendor}':\n  " + "\n  ".join(notes),
            parent_id=parent_id,
            metadata={
                "vendor": vendor,
                "vendor_trust_tier": trust_tier,
                "vendor_trust_label": tier_label,
                "test_count": test_count,
                "notes": "; ".join(notes),
            },
        )


# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------

def _demo():
    """Run the protocol against real BPC-157 data and print the trace."""
    import os

    # Load real data from peptide-checker database
    data_path = os.path.join(
        os.path.expanduser("~"),
        "peptide-checker", "data", "bpc157", "finnrick_ratings.json",
    )
    if os.path.exists(data_path):
        with open(data_path, "r") as f:
            all_vendors = json.load(f)
    else:
        # Fallback: inline sample
        all_vendors = [
            {
                "peptide_name": "BPC-157",
                "vendor": "Peptide Partners",
                "grade": "A",
                "score_avg": 8.0,
                "score_min": 6.9,
                "score_max": 10.0,
                "test_count": 7,
                "tentative": False,
                "source": "finnrick",
                "notes": "Highest confidence A-rated vendor",
            }
        ]

    protocol = PeptideQualityProtocol()

    # --- Single result trace ---
    print("=" * 72)
    print("PEPTIDE QUALITY PROTOCOL — Single Result Trace")
    print("=" * 72)

    # Pick a high-quality vendor and a low-quality vendor
    good_vendor = next(
        (v for v in all_vendors if v.get("grade") == "A"), all_vendors[0]
    )
    bad_vendor = next(
        (v for v in all_vendors if v.get("grade") == "E"), all_vendors[-1]
    )

    for label, test_data in [("GOOD", good_vendor), ("BAD", bad_vendor)]:
        print(f"\n{'—' * 72}")
        print(f"  {label} VENDOR: {test_data.get('vendor')}")
        print(f"{'—' * 72}")
        trace = protocol.evaluate_test_result(test_data)

        # Print each step
        for step in trace.steps:
            print(f"\n  [{step.type.value.upper()}] (id={step.id})")
            for line in step.content.split("\n"):
                print(f"    {line}")
            if step.confidence is not None:
                print(f"    confidence: {step.confidence:.2f}")

        print(f"\n  Trace outcome: {trace.outcome}")

        # Validate against protocol
        violations = protocol.validate_trace(trace)
        if violations:
            print(f"  VIOLATIONS: {violations}")
        else:
            print("  Protocol validation: PASSED")

    # --- Vendor comparison trace ---
    print(f"\n\n{'=' * 72}")
    print("PEPTIDE QUALITY PROTOCOL — Vendor Comparison Trace")
    print("=" * 72)

    comparison_trace = protocol.compare_vendors(all_vendors)
    for step in comparison_trace.steps:
        print(f"\n  [{step.type.value.upper()}] (id={step.id})")
        for line in step.content.split("\n"):
            print(f"    {line}")

    print(f"\n  Comparison outcome: {comparison_trace.outcome}")

    # --- Degradation risk trace ---
    print(f"\n\n{'=' * 72}")
    print("PEPTIDE QUALITY PROTOCOL — Degradation Risk Trace")
    print("=" * 72)

    risky_storage = {
        "temp_c": 25,
        "reconstituted": True,
        "days_since_reconstitution": 45,
        "light_exposure": True,
    }
    risk_trace = protocol.assess_degradation_risk("BPC-157", risky_storage)
    for step in risk_trace.steps:
        print(f"\n  [{step.type.value.upper()}] (id={step.id})")
        for line in step.content.split("\n"):
            print(f"    {line}")

    print(f"\n  Risk outcome: {risk_trace.outcome}")

    # --- Print the full JSON trace for the good vendor ---
    print(f"\n\n{'=' * 72}")
    print("FULL JSON TRACE (good vendor)")
    print("=" * 72)
    good_trace = protocol.evaluate_test_result(good_vendor)
    print(good_trace.to_json())


if __name__ == "__main__":
    _demo()
