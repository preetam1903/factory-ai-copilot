# ==========================================================
# CONTEXT AGENT
# ==========================================================

import re


class ContextAgent:

    def investigate(self, question: str):

        question = question.strip()

        weeks = 3

        match = re.search(r"(\d+)\s*week", question.lower())

        if match:
            weeks = int(match.group(1))

        return {

            "business_question": question,

            "requested_window": f"Last {weeks} Weeks",

            "trend_window": "Last 5 Weeks",

            "investigation_weeks": weeks,

            "objective":
                "Identify operational evidence explaining the production trend.",

            "datasets": [
                "Production",
                "Shift Reports"
            ]
        }


if __name__ == "__main__":

    agent = ContextAgent()

    result = agent.investigate(
        "Why has production reduced over the last 3 weeks?"
    )

    print(result)
