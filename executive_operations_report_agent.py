import streamlit as st
from openai import OpenAI
from datetime import datetime


class ExecutiveOperationsReportAgent:

    def __init__(self):

        self.client = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"]
        )

    def investigate(
        self,
        correlation_result,
        investigation_period="Week Under Investigation",
        reference_period="Previous Comparison Period",
        plant="Hot Strip Mill"
    ):

        generated_time = datetime.now().strftime("%d-%b-%Y %H:%M")

        header = f"""
=========================================================
            OPERATIONS INTELLIGENCE REPORT
=========================================================

Investigation
Production Reduction Investigation

Investigation Period
{investigation_period}

Reference Period
{reference_period}

Plant
{plant}

Status
🔴 Investigation Complete

Generated On
{generated_time}

=========================================================
"""

        # -------------------------------------------------
        # Format Intelligence Blocks
        # -------------------------------------------------

        downtime = correlation_result["downtime_intelligence"]

        downtime_text = f"""
Total Downtime : {downtime['total_hours']} hrs

Planned Downtime :
    {downtime['planned_hours']} hrs ({downtime['planned_percentage']}%)

Unplanned Downtime :
    {downtime['unplanned_hours']} hrs ({downtime['unplanned_percentage']}%)
"""

        trend = correlation_result["trend_intelligence"]

        trend_text = f"""
Investigation Hours : {trend['investigation_hours']} hrs
Reference Hours     : {trend['reference_hours']} hrs
Change              : {trend['change_hours']} hrs
Variation           : {trend['change_percentage']}%
Status              : {trend['status']}
"""

        shift_text = ""

        for shift, values in correlation_result["shift_intelligence"].items():

            shift_text += (
                f"{shift}: "
                f"{values['hours']} hrs "
                f"({values['percentage']}%)\n"
            )

        equipment_text = ""

        for eq, values in correlation_result["equipment_intelligence"].items():

            equipment_text += (
                f"{eq}: "
                f"{values['hours']} hrs "
                f"({values['percentage']}%)\n"
            )

        prompt = f"""
You are an experienced Steel Plant Operations Director.

Prepare a professional Executive Operations Investigation Report.

Use the following report header exactly.

{header}

=========================================================
EXECUTIVE KPI DASHBOARD
=========================================================

Production Loss
{correlation_result["total_loss_tonnes"]} tonnes

Critical Equipment
{correlation_result["critical_equipment"]}

Critical Shift
{correlation_result["critical_shift"]}

Business Risk

HIGH if production loss > 5000 tonnes

MEDIUM if production loss between 2000–5000 tonnes

LOW otherwise

AI Confidence

Estimate confidence based on completeness of supplied evidence.

=========================================================
FACTS
=========================================================

Trend Intelligence

{trend_text}

Downtime Intelligence

{downtime_text}

Shift Intelligence

{shift_text}

Equipment Intelligence

{equipment_text}

Issue Distribution

{correlation_result["issue_distribution"]}

Severity Distribution

{correlation_result["severity_distribution"]}

Production Impact Distribution

{correlation_result["impact_distribution"]}

Root Causes

{correlation_result["root_causes"]}

Key Findings

{correlation_result["findings"]}

Evidence

{correlation_result["evidence"]}

=========================================================
REPORT FORMAT
=========================================================

Generate the report in exactly the following order.

1. Executive KPI Dashboard

2. AI Operational Alerts
   - Maximum 5 alerts
   - Alert
   - Evidence
   - Business Impact

3. Trend Intelligence
   - Summarize the trend.
   - Explain whether performance improved or deteriorated.

4. Downtime Intelligence
   - Planned vs Unplanned downtime.
   - Comment on operational stability.

5. Shift Intelligence
   - Show highest contributing shift.
   - Explain likely operational implication.

6. Equipment Intelligence
   - Show highest contributing equipment.
   - Explain business impact.

7. Executive Summary

8. Key Findings

9. Business Impact

10. Immediate Actions

11. Long-Term Recommendations

12. AI Confidence & Evidence

Rules

• Use only supplied evidence.

• Do not invent facts.

• Keep language executive level.

• Use bullets wherever possible.

• Highlight critical observations using 🔴 🟠 🟢.

"""

        response = self.client.chat.completions.create(

            model="gpt-5",

            messages=[
                {
                    "role": "system",
                    "content": "You are an experienced Steel Plant Operations Director."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

        )

        report = header + "\n\n" + response.choices[0].message.content

        return {

            "report": report

        }
