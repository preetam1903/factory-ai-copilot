import streamlit as st

from openai import OpenAI


class ExecutiveOperationsReportAgent:

    def __init__(self):

        self.client = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"]
        )

    def investigate(self, correlation_result):

        prompt = f"""
You are a Manufacturing COO.

Prepare an Executive Investigation Report.

Facts

Critical Equipment:
{correlation_result["critical_equipment"]}

Critical Shift:
{correlation_result["critical_shift"]}

Estimated Production Loss:
{correlation_result["total_loss_tonnes"]} tonnes

Issue Distribution:
{correlation_result["issue_distribution"]}

Severity Distribution:
{correlation_result["severity_distribution"]}

Production Impact Distribution:
{correlation_result["impact_distribution"]}

Root Causes:
{correlation_result["root_causes"]}

Key Findings:
{correlation_result["findings"]}

Prepare the report in the following format.

1. Executive Summary

2. Key Findings

3. Business Impact

4. Immediate Actions

5. Long-Term Recommendations

Use bullet points.

Do not invent facts.

Use only the supplied evidence.
"""

        response = self.client.chat.completions.create(

            model="gpt-5",

            messages=[

                {
                    "role": "system",
                    "content":
                    "You are an experienced Steel Plant Operations Director."
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ]

            

        )

        report = response.choices[0].message.content

        return {

            "report": report

        }
