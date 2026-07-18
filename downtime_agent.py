import pandas as pd


class DowntimeAgent:

    def __init__(self, downtime_df):
        self.df = downtime_df.copy()

        # Standardized date column
        self.df["DATE"] = pd.to_datetime(self.df["DATE"])

        # Downtime in hours
        self.df["Downtime Hrs"] = self.df["Duration (min)"] / 60

    def investigate(self, start_date, end_date):

        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # ----------------------------------------
        # Investigation Period
        # ----------------------------------------
        period = self.df[
            (self.df["DATE"] >= start_date) &
            (self.df["DATE"] <= end_date)
        ]

        # ----------------------------------------
        # Reference Period (Previous 14 Days)
        # ----------------------------------------
        reference = self.df[
            (self.df["DATE"] < start_date) &
            (self.df["DATE"] >= start_date - pd.Timedelta(days=14))
        ]

        # ----------------------------------------
        # Investigation Summary
        # ----------------------------------------
        total_dt = period["Downtime Hrs"].sum()

        planned_dt = period.loc[
            period["Event Type"] == "Planned",
            "Downtime Hrs"
        ].sum()

        unplanned_dt = period.loc[
            period["Event Type"] == "Unplanned",
            "Downtime Hrs"
        ].sum()

        # ----------------------------------------
# Downtime Percentages
# ----------------------------------------
        if total_dt > 0:
            planned_pct = round((planned_dt / total_dt) * 100, 1)
            unplanned_pct = round((unplanned_dt / total_dt) * 100, 1)
        else:
            planned_pct = 0
            unplanned_pct = 0

        # ----------------------------------------
        # Downtime By Shift
        # ----------------------------------------
        downtime_by_shift = (
            period.groupby("SHIFT")["Downtime Hrs"]
            .sum()
            .sort_values(ascending=False)
            .to_dict()
        )

        # ----------------------------------------
        # Downtime By Equipment
        # ----------------------------------------
        downtime_by_equipment = (
            period.groupby("Equipment")["Downtime Hrs"]
            .sum()
            .sort_values(ascending=False)
            .to_dict()
        )

        # ----------------------------------------
        # Downtime By Department
        # ----------------------------------------
        downtime_by_department = (
            period.groupby("Department")["Downtime Hrs"]
            .sum()
            .sort_values(ascending=False)
            .to_dict()
        )

        # ----------------------------------------
        # Operator Remarks
        # ----------------------------------------
        downtime_by_remark = (
            period.groupby("Operator Remarks")["Downtime Hrs"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .to_dict()
        )

        # ----------------------------------------
        # Reference Summary
        # ----------------------------------------
        ref_total = reference["Downtime Hrs"].sum()

        ref_planned = reference.loc[
            reference["Event Type"] == "Planned",
            "Downtime Hrs"
        ].sum()

        

        ref_unplanned = reference.loc[
            reference["Event Type"] == "Unplanned",
            "Downtime Hrs"
        ].sum()

        if ref_total > 0:
            ref_planned_pct = round((ref_planned / ref_total) * 100, 1)
            ref_unplanned_pct = round((ref_unplanned / ref_total) * 100, 1)
        else:
            ref_planned_pct = 0
            ref_unplanned_pct = 0

        # ----------------------------------------
        # Executive Summary
        # ----------------------------------------
        summary = (
            f"Investigation period recorded {total_dt:.1f} hrs downtime "
            f"({planned_dt:.1f} hrs planned, "
            f"{unplanned_dt:.1f} hrs unplanned). "
            f"Reference period recorded {ref_total:.1f} hrs downtime."
        )

        return {

            "summary": summary,

            "investigation": {

                "total_downtime": round(total_dt, 2),
                "planned_downtime": round(planned_dt, 2),
                "planned_percentage": planned_pct,

                "unplanned_downtime": round(unplanned_dt, 2),
                "unplanned_percentage": unplanned_pct,

                "downtime_by_shift": downtime_by_shift,
                "downtime_by_department": downtime_by_department,
                "downtime_by_equipment": downtime_by_equipment,
                "top_operator_remarks": downtime_by_remark,

            },

            "reference": {

                "total_downtime": round(ref_total, 2),
                "planned_downtime": round(ref_planned, 2),
                "planned_percentage": ref_planned_pct,

                "unplanned_downtime": round(ref_unplanned, 2),
                "unplanned_percentage": ref_unplanned_pct,

            }

        }
