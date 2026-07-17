# shift_agent.py

from production_service import ProductionService


class ShiftAgent:
    def __init__(self):
        self.service = ProductionService()

    def investigate(self, date):

        production = self.service.production.copy()
        production["DATE"] = production["DATE"].dt.date

        plan = self.service.plan.copy()
        plan["DATE"] = plan["DATE"].dt.date

        date = date.date() if hasattr(date, "date") else date

        prod = production[production["DATE"] == date]
        plan = plan[plan["DATE"] == date]

        shift_actual = (
            prod.groupby("SHIFT", as_index=False)
            .agg({"ACTUAL_TONNAGE": "sum"})
        )

        shift_plan = (
            plan.groupby("SHIFT", as_index=False)
            .agg({"PLAN_TONNAGE": "sum"})
        )

        summary = shift_plan.merge(
            shift_actual,
            on="SHIFT",
            how="left"
        ).fillna(0)

        summary["LOSS"] = (
            summary["PLAN_TONNAGE"]
            - summary["ACTUAL_TONNAGE"]
        )

        worst_shift = summary.loc[summary["LOSS"].idxmax()]

        reports = self.service.shift[
            (self.service.shift["DATE"].dt.date == date)
            &
            (self.service.shift["SHIFT"] == worst_shift["SHIFT"])
        ]

        return {
            "date": date,
            "shift_summary": summary,
            "worst_shift": worst_shift["SHIFT"],
            "planned": float(worst_shift["PLAN_TONNAGE"]),
            "actual": float(worst_shift["ACTUAL_TONNAGE"]),
            "loss": float(worst_shift["LOSS"]),
            "reports": reports,
            "recommendation": f"Analyse operational events for Shift {worst_shift['SHIFT']}."
        }


if __name__ == "__main__":

    agent = ShiftAgent()

    result = agent.investigate("2026-06-18")

    print("\n========== SHIFT INVESTIGATION ==========\n")
    print(result["shift_summary"])
    print("\n----------------------------------------")
    print("Worst Shift :", result["worst_shift"])
    print("Loss        :", result["loss"])
    print(result["recommendation"])
