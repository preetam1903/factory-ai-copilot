# ==========================================================
# TREND AGENT
# ==========================================================

from production_service import ProductionService


class TrendAgent:

    def __init__(self):

        self.service = ProductionService()

    # =====================================================
    # Trend Investigation
    # =====================================================

    def investigate(self, context):

        investigation_weeks = context["investigation_weeks"]

        summary = self.service.get_12_week_summary().copy()

        summary = summary.sort_values("WEEK_NO").reset_index(drop=True)

        # --------------------------------------------------
        # Additional Metrics
        # --------------------------------------------------

        summary["ACHIEVEMENT"] = (
            summary["ACTUAL_TONNAGE"]
            / summary["PLAN_TONNAGE"]
            * 100
        ).round(1)

        summary["LOSS"] = (
            summary["PLAN_TONNAGE"]
            - summary["ACTUAL_TONNAGE"]
        )

        summary["ROLLING_ACTUAL"] = (
            summary["ACTUAL_TONNAGE"]
            .rolling(4, min_periods=1)
            .mean()
        )

        summary["PLAN_CHANGE_%"] = (
            summary["PLAN_TONNAGE"]
            .pct_change()
            * 100
        ).round(1)

        summary["ACTUAL_CHANGE_%"] = (
            summary["ACTUAL_TONNAGE"]
            .pct_change()
            * 100
        ).round(1)

        summary["ROLLING_CHANGE_%"] = (
            (
                summary["ACTUAL_TONNAGE"]
                - summary["ROLLING_ACTUAL"]
            )
            /
            summary["ROLLING_ACTUAL"]
            * 100
        ).round(1)

        # --------------------------------------------------
        # Investigation Window
        # --------------------------------------------------

        investigation = summary.tail(investigation_weeks)

        # --------------------------------------------------
# Investigation Context
# --------------------------------------------------

        latest_week = int(summary.iloc[-1]["WEEK_NO"])

        start_week = int(investigation.iloc[0]["WEEK_NO"])

        analysis_start = max(
            int(summary.iloc[0]["WEEK_NO"]),
            start_week - 3
        )

        question = context.get(
            "question",
            "How has HSM production been?"
        )

        question_lower = question.lower()

        if "why" in question_lower:

            question_type = "Investigation"

        elif "how" in question_lower:

            question_type = "Performance Review"

        elif "compare" in question_lower:

            question_type = "Comparison"

        elif "stable" in question_lower:

            question_type = "Assessment"

        else:

            question_type = "General Review"

        assumption = None

        if "reduced" in question_lower:

            assumption = "Production Reduced"

        elif "increase" in question_lower:

            assumption = "Production Increased"

        analysis_window = summary[
            summary["WEEK_NO"] >= analysis_start
        ].copy()

        ###################

        total_plan = investigation["PLAN_TONNAGE"].sum()

        total_actual = investigation["ACTUAL_TONNAGE"].sum()

        total_loss = investigation["LOSS"].sum()

        achievement = round(
            total_actual / total_plan * 100,
            1
        )

        # --------------------------------------------------
        # Best / Worst Week
        # --------------------------------------------------

        best_week = summary.loc[
            summary["ACTUAL_TONNAGE"].idxmax()
        ]

        worst_week = summary.loc[
            summary["ACTUAL_TONNAGE"].idxmin()
        ]

        # --------------------------------------------------
# Requested Period Trend
# --------------------------------------------------

        requested = investigation["ACTUAL_TONNAGE"]

        if requested.is_monotonic_increasing:

            requested_trend = "Improving"

        elif requested.is_monotonic_decreasing:

            requested_trend = "Declining"

        else:

            requested_trend = "Fluctuating"

        # --------------------------------------------------
# Overall Analysis Trend
# --------------------------------------------------

        analysis_actual = analysis_window["ACTUAL_TONNAGE"]

        highest = analysis_actual.max()

        lowest = analysis_actual.min()

        highest_idx = analysis_actual.idxmax()

        lowest_idx = analysis_actual.idxmin()

        if highest_idx < lowest_idx:

            overall_pattern = "Decline"

        elif lowest_idx < highest_idx:

            overall_pattern = "Recovery"

        else:

            overall_pattern = "Stable"

        # --------------------------------------------------
# Largest Week-on-Week Drop
# --------------------------------------------------

        wow = summary["ACTUAL_CHANGE_%"]

        largest_drop_idx = wow.idxmin()

        largest_drop = wow.min()

        drop_week = int(summary.loc[largest_drop_idx, "WEEK_NO"])

        # --------------------------------------------------
# Recovery Detection
# --------------------------------------------------

        recovery = False

        recovery_start = None

        recent_changes = summary.tail(3)["ACTUAL_CHANGE_%"]

        if (recent_changes > 0).all():

            recovery = True

            recovery_start = int(summary.iloc[-3]["WEEK_NO"])

        # --------------------------------------------------
# Investigation Assessment
# --------------------------------------------------

        assessment_status = "General Review"

        if assumption == "Production Reduced":

            if requested_trend == "Declining":

                assessment_status = "Supported"

            else:

                assessment_status = "Not Supported"

        elif assumption == "Production Increased":

            if requested_trend == "Improving":

                assessment_status = "Supported"

            else:

                assessment_status = "Not Supported"
        # --------------------------------------------------
        # Trend Start
        # --------------------------------------------------

        trend_start = int(
            investigation.iloc[0]["WEEK_NO"]
        )

        # --------------------------------------------------
        # Previous Week Comparison
        # --------------------------------------------------

        latest = summary.iloc[-1]

        previous = summary.iloc[-2]

        previous_week_change = round(

            (
                latest["ACTUAL_TONNAGE"]
                - previous["ACTUAL_TONNAGE"]
            )
            /
            previous["ACTUAL_TONNAGE"]
            * 100,

            1

        )

        # --------------------------------------------------
        # Rolling Average Comparison
        # --------------------------------------------------

        rolling_change = round(

            (
                latest["ACTUAL_TONNAGE"]
                - latest["ROLLING_ACTUAL"]
            )
            /
            latest["ROLLING_ACTUAL"]
            * 100,

            1

        )

        # --------------------------------------------------
        # Plan Stability
        # --------------------------------------------------

        plan_change = round(

            investigation["PLAN_CHANGE_%"]
            .fillna(0)
            .abs()
            .mean(),

            1

        )

        if plan_change < 2:

            plan_status = "Stable"

        else:

            plan_status = "Changed"

        # --------------------------------------------------
        # Severity
        # --------------------------------------------------

        gap = abs(rolling_change)

        if gap < 3:

            severity = "Minor"

        elif gap < 7:

            severity = "Moderate"

        elif gap < 12:

            severity = "Major"

        else:

            severity = "Critical"

        # --------------------------------------------------
        # Confidence
        # --------------------------------------------------

        confidence = "Medium"

        if (
            trend == "Declining"
            and plan_status == "Stable"
            and gap > 7
        ):

            confidence = "High"

        # --------------------------------------------------
# Investigation Facts
# --------------------------------------------------

        trend_facts = {

            "question": question,

            "question_type": question_type,

            "assumption": assumption,

            "assessment_status": assessment_status,

            "requested_period": f"Week {start_week} - Week {latest_week}",

            "analysis_period": f"Week {analysis_start} - Week {latest_week}",

            "requested_trend": requested_trend,

            "overall_pattern": overall_pattern,

            "plan_status": plan_status,

            "achievement": achievement,

            "production_loss": int(total_loss),

            "largest_drop_week": drop_week,

            "largest_drop_percent": float(largest_drop),

            "recovery_detected": recovery,

            "recovery_start": recovery_start,

            "rolling_average_change": rolling_change,

            "previous_week_change": previous_week_change,

            "severity": severity,

            "confidence": confidence

        }

        # --------------------------------------------------
        # AI Assessment
        # --------------------------------------------------

        assessment = f"""
Production planning remained {plan_status.lower()} during the selected period.

Actual production shows a {trend.lower()} trend.

Production changed by {previous_week_change:.1f}% compared to the previous week.

Current production is {rolling_change:.1f}% compared to the rolling 4-week average.

Overall achievement against plan is {achievement:.1f}%.

The first significant deterioration is considered to have started in Week {trend_start}.

This behaviour indicates an operational execution issue rather than a reduction in production planning.

Recommended investigation should focus on Weeks {trend_start} to {int(latest['WEEK_NO'])}.
"""

        # --------------------------------------------------
        # Investigation Rules
        # --------------------------------------------------

        findings = []

        if plan_status == "Stable":

            findings.append(
                "Production plan remained stable."
            )

        else:

            findings.append(
                "Production plan changed."
            )

        if previous_week_change < 0:

            findings.append(
                f"Production reduced by {abs(previous_week_change):.1f}% compared with previous week."
            )

        if rolling_change < 0:

            findings.append(
                f"Production is {abs(rolling_change):.1f}% below the rolling four-week average."
            )

        findings.append(
            f"Overall achievement against plan is {achievement:.1f}%."
        )

        # --------------------------------------------------
        # Return
        # --------------------------------------------------

        return {

            "question": question,

            "question_type": question_type,

            "assumption": assumption,

            "investigation_period": {

                "start_week": start_week,

                "end_week": latest_week

            },

            "analysis_period": {

                "start_week": analysis_start,

                "end_week": latest_week

            },

            "trend_facts": trend_facts,

            "requested_trend": requested_trend,

            "overall_pattern": overall_pattern,

            "largest_drop": {

                "week": drop_week,

                "change": largest_drop

            },

            "recovery_detected": recovery,

            "recovery_start": recovery_start,

            "assessment_status": assessment_status,

            "severity": severity,

            "confidence": confidence,

            "plan_status": plan_status,

            "achievement": achievement,

            "loss": total_loss,

            "best_week": int(best_week["WEEK_NO"]),

            "worst_week": int(worst_week["WEEK_NO"]),

            "trend_start": trend_start,

            "previous_week_change": previous_week_change,

            "rolling_average_change": rolling_change,

            "recommended_window": {

                "weeks": investigation_weeks,

                "start_week": trend_start,

                "end_week": int(latest["WEEK_NO"]),

                "label": f"Week {trend_start} - Week {int(latest['WEEK_NO'])}"

            },

            "assessment": assessment,

            "findings": findings,

            "chart": summary

        }


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    context = {

        "investigation_weeks": 3

    }

    agent = TrendAgent()

    result = agent.investigate(context)

    print(result["assessment"])

    print()

    for item in result["findings"]:

        print("-", item)
