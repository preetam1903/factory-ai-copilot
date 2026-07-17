# services/production_service.py

from pathlib import Path
import pandas as pd


class ProductionService:
    def __init__(
        self,
        production_file="COIL_OPERATION_FACT.xlsx",
        plan_file="PRODUCTION_PLAN.xlsx",
        shift_file="SHIFT_REPORT.xlsx",
    ):
        self.production = pd.read_excel(Path(production_file))
        self.plan = pd.read_excel(Path(plan_file))
        self.shift = pd.read_excel(Path(shift_file))

        self._prepare_data()

    def _prepare_data(self):

    # -----------------------------
    # Production Dataset
    # -----------------------------
        self.production.rename(
            columns={
                "PROD_DATE": "DATE",
                "COIL_WEIGHT_TON": "ACTUAL_TONNAGE"
            },
            inplace=True
        )

        self.production["DATE"] = pd.to_datetime(self.production["DATE"])
        self.production["WEEK_NO"] = self.production["DATE"].dt.isocalendar().week.astype(int)

    # -----------------------------
    # Production Plan Dataset
    # -----------------------------
        self.plan.rename(
            columns={
                "Date": "DATE",
                "Week": "WEEK_NO",
                "Planned Production (t)": "PLAN_TONNAGE"
            },
            inplace=True
        )

        self.plan["DATE"] = pd.to_datetime(self.plan["DATE"])

        self.plan["WEEK_NO"] = (
            self.plan["WEEK_NO"]
            .astype(str)
            .str.replace("W", "", regex=False)
            .astype(int)
        )

    # -----------------------------
    # Shift Report Dataset
    # -----------------------------
        self.shift.rename(
            columns={
                "Date": "DATE",
                "Shift": "SHIFT"
            },
            inplace=True
        )

        self.shift["DATE"] = pd.to_datetime(self.shift["DATE"])

    # -------------------------------------------------------
    # Executive Summary (12 Weeks)
    # -------------------------------------------------------

    def get_12_week_summary(self):

        weekly_actual = (
            self.production.groupby("WEEK_NO")["ACTUAL_TONNAGE"]
            .sum()
            .reset_index()
        )

        weekly_plan = (
            self.plan.groupby("WEEK_NO")["PLAN_TONNAGE"]
            .sum()
            .reset_index()
        )

        summary = weekly_plan.merge(
            weekly_actual,
            on="WEEK_NO",
            how="left"
        ).fillna(0)

        summary["LOSS"] = (
            summary["PLAN_TONNAGE"] -
            summary["ACTUAL_TONNAGE"]
        )

        summary = summary.sort_values("WEEK_NO")

        return summary

    # -------------------------------------------------------
    # Dynamic Investigation Window
    # -------------------------------------------------------

    def get_last_n_weeks(self, n):

        summary = self.get_12_week_summary()

        return summary.tail(n).reset_index(drop=True)

    # -------------------------------------------------------
    # Week Details
    # -------------------------------------------------------

    def get_week_details(self, week_no):

        prod = self.production[
            self.production["WEEK_NO"] == week_no
        ].copy()

        plan = self.plan[
            self.plan["WEEK_NO"] == week_no
        ].copy()

        planned = plan["PLAN_TONNAGE"].sum()
        actual = prod["ACTUAL_TONNAGE"].sum()

        return {
            "week": week_no,
            "planned": planned,
            "actual": actual,
            "loss": planned - actual,
            "daily_data": prod
        }

    # -------------------------------------------------------
    # Day Details
    # -------------------------------------------------------

    def get_day_details(self, date):

        date = pd.to_datetime(date)

        prod = self.production[
            self.production["DATE"] == date
        ].copy()

        plan = self.plan[
            self.plan["DATE"] == date
        ].copy()

        planned = plan["PLAN_TONNAGE"].sum()
        actual = prod["ACTUAL_TONNAGE"].sum()

        return {
            "date": date,
            "planned": planned,
            "actual": actual,
            "loss": planned - actual,
            "shift_data": prod
        }

    # -------------------------------------------------------
    # Shift Details
    # -------------------------------------------------------

    def get_shift_details(self, date, shift):

        date = pd.to_datetime(date)

        prod = self.production[
            (self.production["DATE"] == date)
            & (self.production["SHIFT"] == shift)
        ].copy()

        plan = self.plan[
            (self.plan["DATE"] == date)
            & (self.plan["SHIFT"] == shift)
        ].copy()

        planned = plan["PLAN_TONNAGE"].sum()
        actual = prod["ACTUAL_TONNAGE"].sum()

        reports = self.shift[
            (self.shift["DATE"] == date)
            & (self.shift["SHIFT"] == shift)
        ].copy()

        return {
            "date": date,
            "shift": shift,
            "planned": planned,
            "actual": actual,
            "loss": planned - actual,
            "reports": reports
        }

    # -------------------------------------------------------
    # Utility
    # -------------------------------------------------------

    def calculate_production_loss(self, planned, actual):
        return planned - actual

    def calculate_plan_vs_actual(self):
        summary = self.get_12_week_summary()

        return summary[
            [
                "WEEK_NO",
                "PLAN_TONNAGE",
                "ACTUAL_TONNAGE",
                "LOSS",
            ]
        ]
