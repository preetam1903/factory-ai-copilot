# day_agent.py

from production_service import ProductionService


class DayAgent:
    def __init__(self):
        self.service = ProductionService()

    def investigate(self, week_no):

        week = self.service.get_week_details(week_no)

        daily = week["daily_data"].copy()

        if daily.empty:
            return {
                "status": "No daily data found."
            }

        daily = (
            daily.groupby("DATE", as_index=False)
            .agg(
                {
                    "ACTUAL_TONNAGE": "sum"
                }
            )
        )

        plan = self.service.plan
        week_plan = plan[plan["WEEK_NO"] == week_no]

        day_plan = (
            week_plan.groupby("DATE", as_index=False)
            .agg(
                {
                    "PLAN_TONNAGE": "sum"
                }
            )
        )

        summary = day_plan.merge(
            daily,
            on="DATE",
            how="left"
        ).fillna(0)

        summary["LOSS"] = (
            summary["PLAN_TONNAGE"]
            - summary["ACTUAL_TONNAGE"]
        )

        worst_day = summary.loc[summary["LOSS"].idxmax()]

        return {
            "week": week_no,
            "daily_summary": summary,
            "worst_day": worst_day["DATE"],
            "planned": float(worst_day["PLAN_TONNAGE"]),
            "actual": float(worst_day["ACTUAL_TONNAGE"]),
            "loss": float(worst_day["LOSS"]),
            "recommendation": f"Proceed to investigate {worst_day['DATE'].date()} at shift level."
        }


if __name__ == "__main__":

    agent = DayAgent()

    result = agent.investigate(28)

    print("\n========== DAY INVESTIGATION ==========\n")
    print(result["daily_summary"])
    print("\n----------------------------------------")
    print("Worst Day :", result["worst_day"])
    print("Loss      :", result["loss"])
    print(result["recommendation"])
