# reference_agent.py

from production_service import ProductionService


class ReferenceAgent:
    def __init__(self):
        self.service = ProductionService()

    def investigate(self):

        summary = self.service.get_12_week_summary()

        total_plan = summary["PLAN_TONNAGE"].sum()
        total_actual = summary["ACTUAL_TONNAGE"].sum()
        total_loss = summary["LOSS"].sum()

        best_week = summary.loc[summary["ACTUAL_TONNAGE"].idxmax()]
        worst_week = summary.loc[summary["ACTUAL_TONNAGE"].idxmin()]

        recent = summary.tail(3)

        if recent["ACTUAL_TONNAGE"].is_monotonic_decreasing:
            trend = "Declining"
        elif recent["ACTUAL_TONNAGE"].is_monotonic_increasing:
            trend = "Improving"
        else:
            trend = "Stable"

        narrative = f"""
Executive Production Reference

• Total Planned Production : {total_plan:,.0f} tonnes
• Total Actual Production  : {total_actual:,.0f} tonnes
• Total Production Loss    : {total_loss:,.0f} tonnes

Overall production trend is {trend}.

Best Performing Week:
Week {int(best_week['WEEK_NO'])}
Actual Production : {best_week['ACTUAL_TONNAGE']:,.0f} tonnes

Lowest Performing Week:
Week {int(worst_week['WEEK_NO'])}
Actual Production : {worst_week['ACTUAL_TONNAGE']:,.0f} tonnes

Recommendation:
Investigate the lowest performing weeks to identify operational losses,
maintenance events, inventory constraints and shift level issues.
"""

        return {
            "summary": summary,
            "trend": trend,
            "total_plan": total_plan,
            "total_actual": total_actual,
            "total_loss": total_loss,
            "best_week": int(best_week["WEEK_NO"]),
            "worst_week": int(worst_week["WEEK_NO"]),
            "reference": narrative,
        }


if __name__ == "__main__":

    agent = ReferenceAgent()

    result = agent.investigate()

    print(result["reference"])
