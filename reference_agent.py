from production_service import ProductionService


class ReferenceAgent:

    def __init__(self):
        self.service = ProductionService()

    def investigate(self, investigation_weeks=2):

        summary = self.service.get_12_week_summary()

        total_plan = summary["PLAN_TONNAGE"].sum()
        total_actual = summary["ACTUAL_TONNAGE"].sum()
        total_loss = summary["LOSS"].sum()

        achievement = round(
            (total_actual / total_plan) * 100, 1
        )

        # -------------------------------------------------
# Investigation Window Summary
# -------------------------------------------------

        investigation = summary.tail(investigation_weeks)

        investigation_plan = investigation["PLAN_TONNAGE"].sum()

        investigation_actual = investigation["ACTUAL_TONNAGE"].sum()

        investigation_loss = investigation["LOSS"].sum()

        investigation_achievement = round(
            (investigation_actual / investigation_plan) * 100,
            1
        )

        best_week = summary.loc[
            summary["ACTUAL_TONNAGE"].idxmax()
        ]

        worst_week = summary.loc[
            summary["ACTUAL_TONNAGE"].idxmin()
        ]

        recent = summary.tail(3)

        if recent["ACTUAL_TONNAGE"].is_monotonic_decreasing:
            trend = "Declining"
        elif recent["ACTUAL_TONNAGE"].is_monotonic_increasing:
            trend = "Improving"
        else:
            trend = "Stable"

        start_week = int(summary["WEEK_NO"].min())
        end_week = int(summary["WEEK_NO"].max())

        investigation_start = end_week - investigation_weeks + 1

        assessment = (
            f"Production remained close to plan during the initial weeks. "
            f"A noticeable decline started during Week {investigation_start} "
            f"and continued through Week {end_week}. "
            f"The investigation window has been selected because it contains "
            f"the most significant production deterioration."
        )

        return {

            "investigation": {

                "business_question":
                f"Why has production reduced in the last {investigation_weeks} weeks?",

                "trend_window":
                f"Week {start_week} - Week {end_week}",

                "investigation_window":
                f"Week {investigation_start} - Week {end_week}",

                "purpose":
                "Provide historical production context before beginning the detailed investigation."

            },

            "summary": {

                "planned": total_plan,
                "actual": total_actual,
                "loss": total_loss,
                "achievement": achievement

            },

            "performance": {

                "best_week": int(best_week["WEEK_NO"]),
                "best_actual": best_week["ACTUAL_TONNAGE"],

                "worst_week": int(worst_week["WEEK_NO"]),
                "worst_actual": worst_week["ACTUAL_TONNAGE"],

                "trend": trend

            },

            "assessment": assessment,

            "roadmap": [

                "Weekly Production Analysis",

                "Daily Production Analysis",

                "Shift Performance Analysis",

                "Shift Report Correlation",

                "Executive Root Cause Assessment"

            ],

            "chart": summary

        }


if __name__ == "__main__":

    agent = ReferenceAgent()

    result = agent.investigate()

    print(result)
