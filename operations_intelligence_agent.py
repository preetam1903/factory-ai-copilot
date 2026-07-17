# ==========================================================
# OPERATIONS INTELLIGENCE AGENT
# ==========================================================
import json

import streamlit as st

from openai import OpenAI

from production_service import ProductionService


class OperationsIntelligenceAgent:

    def __init__(self):

        self.service = ProductionService()

        self.client = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"]
        )

    # =====================================================
    # Stage 1
    # Structured Extraction (No LLM)
    # =====================================================

    def extract_downtime(self, row):

        event = {}

        event["date"] = row["DATE"]

        event["shift"] = row["SHIFT"]

        event["planned"] = row.get("PLANNED", False)

        event["start_time"] = row.get("START_TIME")

        event["end_time"] = row.get("END_TIME")

        event["duration_minutes"] = row.get("DURATION_MINUTES")

        event["remarks"] = row.get("REMARKS", "")

        return event

    # =====================================================
    # Stage 2
    # LLM Understanding
    # =====================================================

    def understand_operator(self, remarks):

        if remarks is None:

            remarks = ""

        prompt = f"""
Analyse the following operator shift report.

Operator Remarks

----------------

{remarks}

----------------

Extract the operational information.

Return ONLY JSON.

{{
    "event_type":"",
    "equipment":"",
    "root_cause":"",
    "corrective_action":"",
    "severity":"",
    "production_impact":"",
    "confidence":0.0
}}
"""

        ####################################################
        # Replace this with your OpenAI call
        ####################################################

        try:

            response = self.client.chat.completions.create(

                model="gpt-5",

                messages=[

                    {
                        "role": "system",
                        "content": """
        You are a senior Steel Manufacturing Operations Engineer.

        Your job is to analyse manufacturing shift reports and
        identify operational events that impacted production.

        Return ONLY valid JSON.

        Do not include markdown.

        If information is missing, use empty strings.

        Confidence must be between 0 and 1.
        """
                    },

                    {
                        "role": "user",
                        "content": prompt
                    }

                ],

                response_format={"type": "json_object"}

            )

            result = json.loads(
                response.choices[0].message.content
            )

        except Exception as e:

            print(e)

            result = {

                "event_type": "",

                "equipment": "",

                "root_cause": "",

                "corrective_action": "",

                "severity": "Unknown",

                "production_impact": "",

                "confidence": 0.0

            }

        return result

    # =====================================================
    # Merge Structured + LLM
    # =====================================================

    def merge_event(self, structured, llm):

        return {

            "date":
                structured["date"],

            "shift":
                structured["shift"],

            "planned":
                structured["planned"],

            "start_time":
                structured["start_time"],

            "end_time":
                structured["end_time"],

            "duration_minutes":
                structured["duration_minutes"],

            "event_type":
                llm["event_type"],

            "equipment":
                llm["equipment"],

            "root_cause":
                llm["root_cause"],

            "corrective_action":
                llm["corrective_action"],

            "severity":
                llm["severity"],

            "production_impact":
                llm["production_impact"],

            "confidence":
                llm["confidence"],

            "remarks":
                structured["remarks"]

        }

    # =====================================================
    # Main Investigation
    # =====================================================

    def investigate(self, trend):

        reports = self.service.shift_report.copy()

        start_week = trend["recommended_window"]["start_week"]

        end_week = trend["recommended_window"]["end_week"]

        reports["WEEK_NO"] = (
            reports["DATE"]
            .dt.isocalendar()
            .week.astype(int)
        )

        reports = reports[
            (reports["WEEK_NO"] >= start_week)
            &
            (reports["WEEK_NO"] <= end_week)
        ]

        events = []

        for _, row in reports.iterrows():

            structured = self.extract_downtime(row)

            llm = self.understand_operator(
                structured["remarks"]
            )

            merged = self.merge_event(
                structured,
                llm
            )

            events.append(merged)

        return {

            "events": events

        }


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    trend = {

        "recommended_window": {

            "start_week": 23,

            "end_week": 25

        }

    }

    agent = OperationsIntelligenceAgent()

    result = agent.investigate(trend)

    print(json.dumps(result, indent=4, default=str))
