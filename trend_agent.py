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
        # Trend Detection
        # --------------------------------------------------

        recent = summary.tail(3)

        if recent["ACTUAL_TONNAGE"].is_monotonic_decreasing:

            trend = "Declining"

        elif recent["ACTUAL_TONNAGE"].is_monotonic_increasing:

            trend = "Improving"

        else:

            trend = "Stable"

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

            "trend": trend,

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
