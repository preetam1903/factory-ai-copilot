# week_agent.py

from production_service import ProductionService


class WeekAgent:
    def __init__(self):
        self.service = ProductionService()

    def investigate(self, weeks=5):

        data = self.service.get_last_n_weeks(weeks)

        if data.empty:
            return {
                "status": "No data found."
            }

        worst_week = data.loc[data["LOSS"].idxmax()]

        result = {
            "weeks_requested": weeks,
            "weekly_summary": data,
            "total_plan": data["PLAN_TONNAGE"].sum(),
            "total_actual": data["ACTUAL_TONNAGE"].sum(),
            "total_loss": data["LOSS"].sum(),
            "worst_week": int(worst_week["WEEK_NO"]),
            "worst_week_loss": float(worst_week["LOSS"]),
            "planned": float(worst_week["PLAN_TONNAGE"]),
            "actual": float(worst_week["ACTUAL_TONNAGE"]),
            "recommendation": f"Proceed to investigate Week {int(worst_week['WEEK_NO'])} at day level."
        }

        return result


if __name__ == "__main__":

    agent = WeekAgent()

    result = agent.investigate(5)

    print("\n========== WEEK INVESTIGATION ==========\n")
    print(result["weekly_summary"])
    print("\n----------------------------------------")
    print(f"Total Planned : {result['total_plan']:,.0f}")
    print(f"Total Actual  : {result['total_actual']:,.0f}")
    print(f"Total Loss    : {result['total_loss']:,.0f}")
    print(f"Worst Week    : {result['worst_week']}")
    print(f"Loss          : {result['worst_week_loss']:,.0f}")
    print("\nRecommendation:")
    print(result["recommendation"])
