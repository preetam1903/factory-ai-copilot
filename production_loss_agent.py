import pandas as pd


class ProductionLossAgent:

    def __init__(self, production_rate_tph=250):
        """
        production_rate_tph : Average production rate (Tonnes/Hour)
        """
        self.production_rate = production_rate_tph

    def investigate(self, downtime_df):

        df = downtime_df.copy()

        # ---------------------------------------
        # Ensure DATE is datetime
        # ---------------------------------------
        df["DATE"] = pd.to_datetime(df["DATE"])

        # ---------------------------------------
        # Downtime Hours
        # ---------------------------------------
        df["Downtime Hrs"] = df["Duration (min)"] / 60

        # ---------------------------------------
        # Estimated Production Loss
        # ---------------------------------------
        df["Production Loss (t)"] = (
            df["Downtime Hrs"] * self.production_rate
        )

        # ---------------------------------------
        # Total Loss
        # ---------------------------------------
        total_loss = round(df["Production Loss (t)"].sum(), 2)

        # ---------------------------------------
        # Loss by Equipment
        # ---------------------------------------
        loss_by_equipment = (
            df.groupby("Equipment")["Production Loss (t)"]
            .sum()
            .sort_values(ascending=False)
            .round(2)
            .to_dict()
        )

        # ---------------------------------------
        # Loss by Department
        # ---------------------------------------
        loss_by_department = (
            df.groupby("Department")["Production Loss (t)"]
            .sum()
            .sort_values(ascending=False)
            .round(2)
            .to_dict()
        )

        # ---------------------------------------
        # Loss by Shift
        # ---------------------------------------
        loss_by_shift = (
            df.groupby("SHIFT")["Production Loss (t)"]
            .sum()
            .sort_values(ascending=False)
            .round(2)
            .to_dict()
        )

        # ---------------------------------------
        # Biggest Loss Events
        # ---------------------------------------
        top_events = (
            df.sort_values(
                "Production Loss (t)",
                ascending=False
            )[
                [
                    "DATE",
                    "SHIFT",
                    "Equipment",
                    "Operator Remarks",
                    "Duration (min)",
                    "Production Loss (t)"
                ]
            ]
            .head(10)
            .to_dict("records")
        )

        # ---------------------------------------
        # Executive Summary
        # ---------------------------------------
        summary = (
            f"Estimated production loss was "
            f"{total_loss:.1f} tonnes based on an "
            f"average production rate of "
            f"{self.production_rate} t/hr."
        )

        return {

            "summary": summary,

            "total_loss_tonnes": total_loss,

            "production_rate_tph": self.production_rate,

            "loss_by_equipment": loss_by_equipment,

            "loss_by_department": loss_by_department,

            "loss_by_shift": loss_by_shift,

            "top_loss_events": top_events

        }
