# shift_agent.py

from production_service import ProductionService


class ShiftAgent:

    def __init__(self):
        self.service = ProductionService()

    def investigate(self, date):

        production = self.service.production.copy()
        production["DATE"] = production["DATE"].dt.date

        date = date.date() if hasattr(date, "date") else date

        prod = production[
            production["DATE"] == date
        ].copy()

        if prod.empty:
            return {
                "status": "No production data found."
            }

        # Shift-wise Actual Production
        summary = (
            prod.groupby("SHIFT", as_index=False)
            .agg(
                {
                    "ACTUAL_TONNAGE": "sum"
                }
            )
        )

        summary = summary.sort_values(
            "ACTUAL_TONNAGE"
        ).reset_index(drop=True)

        worst_shift = summary.iloc[0]

        reports = self.service.shift[
            (self.service.shift["DATE"].dt.date == date)
            &
            (self.service.shift["SHIFT"] == worst_shift["SHIFT"])
        ]

        return {

            "date": date,

            "shift_summary": summary,

            "worst_shift": worst_shift["SHIFT"],

            "planned": None,

            "actual": float(
                worst_shift["ACTUAL_TONNAGE"]
            ),

            "loss": 0,

            "reports": reports,

            "recommendation":
                f"Analyse operational events for Shift {worst_shift['SHIFT']}."

        }


if __name__ == "__main__":

    agent = ShiftAgent()

    result = agent.investigate("2026-06-18")

    print("\n========== SHIFT INVESTIGATION ==========\n")

    print(result["shift_summary"])

    print("\n----------------------------------------")

    print("Worst Shift :", result["worst_shift"])

    print("Actual Production :", result["actual"])

    print(result["recommendation"])
