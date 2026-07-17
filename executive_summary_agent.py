# executive_summary_agent.py

from reference_agent import ReferenceAgent
from week_agent import WeekAgent
from day_agent import DayAgent
from shift_agent import ShiftAgent


class ExecutiveSummaryAgent:

    def __init__(self):
        self.reference = ReferenceAgent()
        self.week = WeekAgent()
        self.day = DayAgent()
        self.shift = ShiftAgent()

    def investigate(self, weeks=5):

        ref = self.reference.investigate()

        week = self.week.investigate(weeks)

        day = self.day.investigate(
            week["worst_week"]
        )

        shift = self.shift.investigate(
            day["worst_day"]
        )

        summary = f"""
======================================================
           EXECUTIVE INVESTIGATION SUMMARY
======================================================

Production Trend
----------------
{ref['trend']}

Production Performance
----------------------
Planned Production : {ref['total_plan']:,.0f} tonnes
Actual Production  : {ref['total_actual']:,.0f} tonnes
Production Loss    : {ref['total_loss']:,.0f} tonnes

Investigation Summary
---------------------
Investigation Window : Last {weeks} Weeks

Worst Week
----------
Week : {week['worst_week']}
Loss : {week['worst_week_loss']:,.0f} tonnes

Worst Day
---------
Date : {day['worst_day'].date()}
Loss : {day['loss']:,.0f} tonnes

Worst Shift
-----------
Shift : {shift['worst_shift']}
Loss  : {shift['loss']:,.0f} tonnes

Operational Evidence
--------------------
Shift Reports Analysed : {len(shift['reports'])}

Recommendation
--------------
Perform detailed correlation of:

• Shift Reports
• Maintenance Events
• Inventory Constraints
• Quality Issues
• Equipment Breakdown

to explain the production loss.

======================================================
"""

        return {
            "reference": ref,
            "week": week,
            "day": day,
            "shift": shift,
            "summary": summary
        }


if __name__ == "__main__":

    agent = ExecutiveSummaryAgent()

    result = agent.investigate(5)

    print(result["summary"])
