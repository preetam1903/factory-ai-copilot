import json
import pandas as pd

from datetime import timedelta
from openai import OpenAI


class OperatorEquipmentAgent:

    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def investigate(self, downtime_df):
        downtime_df = (
            downtime_df
            .sort_values("Duration (min)", ascending=False)
            .reset_index(drop=True)
        )

        downtime_df["AI_ID"] = downtime_df.index

        print("\n================ SHIFT REPORT RECEIVED =================")
        print(downtime_df)
        print("========================================================")

        print("\nColumns:")
        print(downtime_df.columns.tolist())

        print("\nImportant fields:")
        print(
            downtime_df[
                [
                    "DATE",
                    "Equipment",
                    "Duration (min)",
                    "Event Type",
                    "Operator Remarks"
                ]
            ]
        )

        rows = []

        # -----------------------------------------------------
        # Build input for AI
        # -----------------------------------------------------

        for _, row in downtime_df.iterrows():

            rows.append({
                "id": int(row["AI_ID"]),
                "equipment": row["Equipment"],
                "department": row["Department"],
                "duration_min": row["Duration (min)"],
                "remarks": row["Operator Remarks"]
            })

        prompt = f"""
You are an experienced steel plant operations engineer.

Analyse each operator remark independently.

Return ONLY valid JSON.

Schema:

[
  {{
    "id":0,
    "equipment":"...",
    "issue_category":"Mechanical/Electrical/Process/Material/Waiting/Maintenance/Quality/Utility/Unknown",
    "severity":"Low/Medium/High/Critical",
    "production_impact":"Low/Medium/High",
    "root_cause":"...",
    "corrective_action":"...",
    "confidence":0.95
  }}
]

Records:

{json.dumps(rows, indent=2)}

Return ONLY JSON.
"""

        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": "You are a manufacturing investigation expert."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # -----------------------------------------------------
        # Parse AI Response
        # -----------------------------------------------------

        try:
            ai_events = json.loads(
                response.choices[0].message.content
            )

            print("\n========== AI RESPONSE ==========")
            print(json.dumps(ai_events, indent=2))
            print("=================================\n")

        except Exception:
            ai_events = []

        # -----------------------------------------------------
        # Merge AI output with original downtime data
        # -----------------------------------------------------

        enriched_events = []

        for event in ai_events:

            idx = event.get("id")

            if idx is None or idx not in downtime_df.index:
                continue

            row = downtime_df[
                downtime_df["AI_ID"] == idx
            ].iloc[0]

            # Build event timestamps
            event_time = pd.to_datetime(
                f"{row['DATE']} {row['Time']}"
            )

            end_time = event_time + timedelta(
                minutes=float(row["Duration (min)"])
            )

            enriched_events.append({

                "id": row["AI_ID"],

                "equipment": row["Equipment"],

                "department": row["Department"],

                "date": event_time.strftime("%Y-%m-%d"),

                "start_time": event_time.strftime("%H:%M:%S"),

                "end_time": end_time.strftime("%H:%M:%S"),

                "duration_minutes": float(row["Duration (min)"]),

                "description": (
                    str(row["Operator Remarks"])
                    if pd.notna(row["Operator Remarks"])
                    else ""
                ),

                "event_type": (
                    row["Event Type"]
                    if pd.notna(row["Event Type"])
                    else event.get("issue_category", "Unknown")
                ),

                "issue_category": event.get(
                    "issue_category",
                    "Unknown"
                ),

                "severity": event.get(
                    "severity",
                    "Unknown"
                ),

                "production_impact": (
                    row["Likely Impact"]
                    if pd.notna(row["Likely Impact"])
                    else event.get("production_impact", "Unknown")
                ),

                "root_cause": (
                    row["Operator Remarks"]
                    if pd.notna(row["Operator Remarks"])
                    and str(row["Operator Remarks"]).strip() != ""
                    else event.get("root_cause", "")
                ),

                "corrective_action": event.get(
                    "corrective_action",
                    ""
                ),

                "confidence": float(
                    event.get(
                        "confidence",
                        0
                    )
                )

            })

        # -----------------------------------------------------
        # Return
        # -----------------------------------------------------

        return {

            "summary": f"AI analysed {len(enriched_events)} operational events.",

            "events": enriched_events

        }
