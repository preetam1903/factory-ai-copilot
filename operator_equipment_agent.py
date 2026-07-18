import json
from openai import OpenAI


class OperatorEquipmentAgent:

    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def investigate(self, downtime_df):

        events = []

        # Build one prompt containing all operator remarks
        rows = []

        for idx, row in downtime_df.iterrows():

            rows.append({
                "id": idx,
                "equipment": row["Equipment"],
                "department": row["Department"],
                "duration_min": row["Duration (min)"],
                "remarks": row["Operator Remarks"]
            })

        prompt = f"""
You are an experienced steel plant operations engineer.

Analyse each operator remark independently.

For every record return ONLY valid JSON.

Return a JSON array.

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
            ],

            temperature=0

        )

        try:

            events = json.loads(response.choices[0].message.content)

        except Exception:

            events = []

        return {

            "summary": f"AI analysed {len(events)} operational events.",

            "events": events

        }
