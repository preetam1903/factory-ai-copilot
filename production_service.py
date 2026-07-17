from pathlib import Path
import pandas as pd


class ProductionService:

    def __init__(
        self,
        production_file="COIL_OPERATION_FACT.xlsx",
        plan_file="PRODUCTION_PLAN.xlsx",
        shift_file="SHIFT_REPORT.xlsx",
    ):

        self.production_file = Path(production_file)
        self.plan_file = Path(plan_file)
        self.shift_file = Path(shift_file)

        self.production = None
        self.daily_plan = None
        self.weekly_plan = None
        self.shift_report = None

        self.load_data()
        self.prepare_data()

    # ----------------------------------------------------
# Last N Weeks
# ----------------------------------------------------

    def get_last_n_weeks(self, n):

        summary = self.get_12_week_summary()

        return (
            summary
            .sort_values("WEEK_NO")
            .tail(n)
            .reset_index(drop=True)
        )

    # ----------------------------------------------------
    # Load Excel Files
    # ----------------------------------------------------

    def load_data(self):

        # Production
        self.production = pd.read_excel(
            self.production_file,
            sheet_name="COIL_OPERATION_FACT"
        )

        # Daily Plan
        self.daily_plan = pd.read_excel(
            self.plan_file,
            sheet_name="DAILY_PLAN"
        )

        # Weekly Plan
        self.weekly_plan = pd.read_excel(
            self.plan_file,
            sheet_name="WEEKLY_PLAN"
        )

        # Shift Report
        self.shift_report = pd.read_excel(
            self.shift_file,
            sheet_name="SHIFT_REPORT"
        )

    # ----------------------------------------------------
    # Prepare Data
    # ----------------------------------------------------

    def prepare_data(self):

        # ---------- Production ----------

        self.production.rename(
            columns={
                "PROD_DATE": "DATE",
                "COIL_WEIGHT_TON": "ACTUAL_TONNAGE"
            },
            inplace=True
        )

        self.production["DATE"] = pd.to_datetime(
            self.production["DATE"]
        )

        self.production["WEEK_NO"] = (
            self.production["DATE"]
            .dt.isocalendar()
            .week.astype(int)
        )

        # ---------- Daily Plan ----------

        self.daily_plan.rename(
            columns={
                "Date": "DATE",
                "Week": "WEEK_NO",
                "Planned Production (t)": "PLAN_TONNAGE"
            },
            inplace=True
        )

        self.daily_plan["DATE"] = pd.to_datetime(
            self.daily_plan["DATE"]
        )

        self.daily_plan["WEEK_NO"] = (
            self.daily_plan["WEEK_NO"]
            .astype(str)
            .str.replace("W", "", regex=False)
            .astype(int)
        )

        # ---------- Weekly Plan ----------

        self.weekly_plan.rename(
            columns={
                "Week": "WEEK_NO",
                "Planned Production (t)": "PLAN_TONNAGE"
            },
            inplace=True
        )

        self.weekly_plan["WEEK_NO"] = (
            self.weekly_plan["WEEK_NO"]
            .astype(str)
            .str.replace("W", "", regex=False)
            .astype(int)
        )

        # ---------- Shift Report ----------

        self.shift_report.rename(
            columns={
                "Date": "DATE",
                "Shift": "SHIFT"
            },
            inplace=True
        )

        self.shift_report["DATE"] = pd.to_datetime(
            self.shift_report["DATE"]
        )

        print("✅ Production rows :", len(self.production))
        print("✅ Daily Plan rows :", len(self.daily_plan))
        print("✅ Weekly Plan rows :", len(self.weekly_plan))
        print("✅ Shift Report rows :", len(self.shift_report))

    # ----------------------------------------------------
# 12 Week Summary
# ----------------------------------------------------

    def get_12_week_summary(self):

        weekly_actual = (
            self.production
            .groupby("WEEK_NO", as_index=False)
            .agg(
                ACTUAL_TONNAGE=("ACTUAL_TONNAGE", "sum")
            )
        )

        weekly_plan = (
            self.daily_plan
            .groupby("WEEK_NO", as_index=False)
            .agg(
                PLAN_TONNAGE=("PLAN_TONNAGE", "sum")
            )
        )

        summary = weekly_plan.merge(
            weekly_actual,
            on="WEEK_NO",
            how="left"
        )

        summary["ACTUAL_TONNAGE"] = summary["ACTUAL_TONNAGE"].fillna(0)

        summary["LOSS"] = (
            summary["PLAN_TONNAGE"]
            - summary["ACTUAL_TONNAGE"]
        )

        summary = summary.sort_values("WEEK_NO")

        return summary
