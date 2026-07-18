# ==========================================================
# CRIME SCENE INVESTIGATION AGENT
# ==========================================================

import pandas as pd
from production_service import ProductionService
import streamlit as st
from openai import OpenAI


class CrimeSceneInvestigationAgent:

    def __init__(self):

        self.service = ProductionService()

        self.client = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"]
        )

        # =====================================================
    # Rank Equipment Related Downtime
    # =====================================================

    def rank_equipment_events(self, operations):

        events = (
            operations
            .get("operator_equipment", {})
            .get("events", [])
        )

        if len(events) == 0:
            return []

        # ---------------------------------------
        # Downtime categories to ignore
        # ---------------------------------------

        ignore_keywords = [

            "power",
            "electricity",
            "plant shutdown",
            "planned",
            "lunch",
            "break",
            "cleaning",
            "housekeeping",
            "general",
            "safety"

        ]

        equipment_events = []

        for event in events:

            text = (
                str(event.get("event_type", "")) + " " +
                str(event.get("equipment", "")) + " " +
                str(event.get("description", ""))
            ).lower()

            ignore = False

            for keyword in ignore_keywords:

                if keyword in text:

                    ignore = True
                    break

            if not ignore:

                equipment_events.append(event)

        # ---------------------------------------
        # Rank by duration
        # ---------------------------------------

        equipment_events = sorted(

            equipment_events,

            key=lambda x: x.get("duration_minutes", 0),

            reverse=True

        )

        suspects = []

        for rank, event in enumerate(equipment_events[:3], start=1):

            suspects.append({

                "rank": rank,

                "equipment":
                    event.get("equipment", "Unknown"),

                "event_type":
                    event.get("event_type", "Unknown"),

                "start_time":
                    event.get("start_time"),

                "end_time":
                    event.get("end_time"),

                "date":
                    event.get("date"),

                "duration_minutes":
                    event.get("duration_minutes", 0),

                "event": event

            })

        return suspects

        # =====================================================
    # Build Investigation Window
    # =====================================================

    def build_investigation_window(self, suspect):

        event = suspect["event"]

        # ---------------------------------------
        # Parse timestamps
        # ---------------------------------------

        start_time = pd.to_datetime(

            f"{event['date']} {event['start_time']}"

        )

        end_time = pd.to_datetime(

            f"{event['date']} {event['end_time']}"

        )

        # ---------------------------------------
        # Investigation Window
        # ---------------------------------------

        before_start = start_time - pd.Timedelta(hours=2)

        after_end = end_time + pd.Timedelta(hours=2)

        return {

            "equipment":
                suspect["equipment"],

            "event_type":
                suspect["event_type"],

            "event_start":
                start_time,

            "event_end":
                end_time,

            "before_start":
                before_start,

            "after_end":
                after_end,

            "duration_minutes":
                suspect["duration_minutes"]

        }
    # =====================================================
    # Read Production Timeline
    # =====================================================

    # =====================================================
# Load Production Inside Investigation Window
# =====================================================

    def get_production_window(self, window):

        production = self.service.production.copy()

        production["DATE"] = pd.to_datetime(production["DATE"])

        start_date = window["before_start"].normalize()

        end_date = window["after_end"].normalize()

        production = production[

            (production["DATE"] >= start_date)
            &
            (production["DATE"] <= end_date)

        ].copy()

        return production

    # =====================================================
# Split Production Timeline
# =====================================================

    def split_production_timeline(self, production, window):

        production = production.copy()

    # If production timestamp is unavailable,
    # use DATE as a fallback.
        production["TIMESTAMP"] = pd.to_datetime(
            production["DATE"]
        )

        before = production[
            production["TIMESTAMP"] < window["event_start"]
        ].copy()

        during = production[
            (production["TIMESTAMP"] >= window["event_start"])
            &
            (production["TIMESTAMP"] <= window["event_end"])
        ].copy()

        after = production[
            production["TIMESTAMP"] > window["event_end"]
        ].copy()

        return {

            "before": before,

            "during": during,

            "after": after

        }

    # =====================================================
# Detect Production Transitions
# =====================================================

    def detect_transitions(self, timeline_data):

        before = timeline_data["before"]
        after = timeline_data["after"]

        transition = {}

        columns = [

            "GRADE",
            "THICKNESS",
            "WIDTH"

        ]

        for column in columns:

            if column not in before.columns:
                continue

            before_values = (
                before[column]
                .dropna()
                .astype(str)
                .value_counts()
                .head(5)
                .to_dict()
            )

            after_values = (
                after[column]
                .dropna()
                .astype(str)
                .value_counts()
                .head(5)
                .to_dict()
            )

            transition[column] = {

                "before": before_values,

                "after": after_values

            }

        return transition


    # =====================================================
# Build Investigation Context
# =====================================================

    def build_investigation_context(
        self,
        suspect,
        window,
        timeline_data,
        transitions,
        reports
    ):

        return {

            "incident": {

                "equipment": suspect["equipment"],
                    "event_type": suspect["event_type"],
            "duration_minutes": suspect["duration_minutes"]

            },

            "window": {
    
                "start": str(window["before_start"]),
                "event_start": str(window["event_start"]),
                "event_end": str(window["event_end"]),
                "end": str(window["after_end"])

            },

            "production": {

                "before": len(timeline_data["before"]),
                "during": len(timeline_data["during"]),
                "after": len(timeline_data["after"])

            },

            "transitions": transitions,

            "operator_remarks":

                reports["Operator Remarks"].dropna().tolist()
                if "Operator Remarks" in reports.columns
                else []

        }

    # =====================================================
# AI Crime Scene Reasoning
# =====================================================

    def ai_reasoning(self, context):

        prompt = f"""
You are a Senior Steel Plant Investigation Engineer with more than 25 years of experience in Hot Strip Mill operations.

You are performing a forensic reconstruction of an operational incident.

Your responsibility is NOT to identify a guaranteed root cause.

Your responsibility is to reconstruct what happened, identify operational changes surrounding the incident, evaluate possible contributing factors, and recommend the next engineering investigations.

=========================================================
INVESTIGATION DATA
=========================================================

{context}

=========================================================
OBJECTIVES
=========================================================

Analyze the supplied evidence and produce an engineering investigation report.

Specifically determine:

• What was happening BEFORE the incident?

• What happened DURING the incident?

• What changed AFTER production restarted?

• Did production mix change?
  - Grade
  - Thickness
  - Width
  - Product family

• Did production transitions begin before the equipment failure?

• Are operator observations consistent with the production changes?

• Could production conditions have contributed to the equipment failure?

• What additional evidence would be required to confirm the hypothesis?

=========================================================
REPORT FORMAT
=========================================================

# Executive Summary

Provide a concise summary of the incident.

---

# Incident Reconstruction

Describe the sequence of events before, during and after the operational disturbance.

---

# Production Before the Incident

Summarize:

• dominant products
• production pattern
• operating conditions
• any unusual observations

---

# Production During the Incident

Explain:

• production interruption
• equipment impact
• production loss
• operational observations

---

# Production After Restart

Describe:

• production recovery
• production mix after restart
• whether production returned to the previous operating state

---

# Product Transition Analysis

Compare before vs after production.

Comment on transitions in:

• Grade
• Thickness
• Width
• Product mix

Highlight significant operational changes.

---

# Operator Correlation

Correlate operator remarks with the production timeline.

Identify observations that support or contradict the production data.

---

# Engineering Assessment

Provide a balanced engineering interpretation.

Explain:

• what evidence supports the assessment

• what evidence is missing

• possible operational explanations

Never overstate certainty.

---

# Possible Contributing Factors

State factors that MAY have contributed.

Use wording such as:

• may indicate

• may have contributed

• could suggest

• is consistent with

Never state that a factor definitely caused the incident.

---

# Recommended Next Investigation

Recommend additional checks such as:

• maintenance history

• alarm history

• hydraulic pressure

• rolling force

• strip tracking

• equipment inspection

• previous similar events

=========================================================
RULES
=========================================================

Use ONLY the supplied investigation evidence.

Do NOT invent facts.

Do NOT fabricate numerical values.

Clearly distinguish facts from engineering interpretation.

If evidence is insufficient, explicitly state that.

Use professional steel manufacturing terminology.

Write in executive report style.

Use Markdown headings and bullet points.

The report should read like it was written by an experienced Operations Investigation Engineer rather than an AI assistant.
"""

        response = self.client.chat.completions.create(

            model="gpt-5",

            messages=[

                {
                    "role": "system",
                    "content":
                    "You are an experienced Steel Plant Investigation Engineer."
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ]

        )

        return response.choices[0].message.content
    # =====================================================
    # Read Shift Reports
    # =====================================================

    def get_shift_window(self, event):

        reports = self.service.shift_report.copy()

        reports["DATE"] = pd.to_datetime(
            reports["DATE"]
        )

        event_date = pd.to_datetime(event["date"])

        reports = reports[
            reports["DATE"] == event_date
        ]

        return reports

    #####################
        # =====================================================
    # Build Crime Scene Timeline
    # =====================================================

    def build_timeline(self, event, production, reports):

        timeline = []

        # ---------------------------------------
        # Incident Entry
        # ---------------------------------------

        timeline.append({
            "time": event.get("start_time", "Unknown"),
            "title": "Major Operational Event",
            "description": event.get(
                "event_type",
                "Production Disturbance"
            )
        })

        # ---------------------------------------
        # Production Statistics
        # ---------------------------------------

        total_coils = len(production)

        total_tonnage = round(
            production["ACTUAL_TONNAGE"].sum(),
            2
        )

        timeline.append({

            "time": "Before Incident",

            "title": "Production Summary",

            "description":
                f"{total_coils} coils processed "
                f"({total_tonnage} tons)"

        })

        # ---------------------------------------
        # Shift Report Remarks
        # ---------------------------------------

        if len(reports) > 0:

            for _, row in reports.iterrows():

                remark = str(
                    row.get("Operator Remarks", "")
                ).strip()

                if remark != "":

                    timeline.append({

                        "time":
                            row.get(
                                "SHIFT",
                                "Shift"
                            ),

                        "title":
                            "Operator Observation",

                        "description":
                            remark

                    })

        # ---------------------------------------
        # Restart
        # ---------------------------------------

        timeline.append({

            "time":
                event.get(
                    "end_time",
                    "Unknown"
                ),

            "title":
                "Production Restart",

            "description":
                "Production resumed after operational interruption."

        })

        return timeline

    #######################
        # =====================================================
    # Build Evidence
    # =====================================================

    def build_evidence(self, event, production, reports):

        evidence = []

        # ---------------------------------------
        # Downtime Duration
        # ---------------------------------------

        duration = event.get("duration_minutes", 0)

        evidence.append({

            "category": "Downtime",

            "finding":
                f"Production interruption lasted {duration} minutes."

        })

        # ---------------------------------------
        # Production Volume
        # ---------------------------------------

        total_coils = len(production)

        total_tonnage = round(
            production["ACTUAL_TONNAGE"].sum(),
            2
        )

        evidence.append({

            "category": "Production",

            "finding":
                f"{total_coils} coils ({total_tonnage} tons) "
                "were processed during the investigation window."

        })

        # ---------------------------------------
        # Shift Report Evidence
        # ---------------------------------------

        if len(reports) > 0:

            remarks = reports["Operator Remarks"] \
                .dropna() \
                .astype(str)

            if len(remarks) > 0:

                evidence.append({

                    "category": "Operator",

                    "finding":
                        remarks.iloc[0]

                })

        # ---------------------------------------
        # Event Severity
        # ---------------------------------------

        severity = event.get(
            "severity",
            "Unknown"
        )

        evidence.append({

            "category": "Severity",

            "finding":
                f"Operational severity classified as {severity}."

        })

        # ---------------------------------------
        # Production Impact
        # ---------------------------------------

        impact = event.get(
            "production_impact",
            ""
        )

        if impact != "":

            evidence.append({

                "category": "Impact",

                "finding":
                    impact

            })

        # ---------------------------------------
        # Root Cause
        # ---------------------------------------

        root = event.get(
            "root_cause",
            ""
        )

        if root != "":

            evidence.append({

                "category": "Root Cause",

                "finding":
                    root

            })

        # ---------------------------------------
        # Confidence
        # ---------------------------------------

        confidence = event.get(
            "confidence",
            0
        )

        evidence.append({

            "category": "Confidence",

            "finding":
                f"AI confidence : {round(confidence*100,1)} %"

        })

        # ---------------------------------------
        # Risk Level
        # ---------------------------------------

        severity = str(
            event.get(
                "severity",
                ""
            )
        ).lower()

        if severity == "high":

            risk = "HIGH"

        elif severity == "medium":

            risk = "MEDIUM"

        else:

            risk = "LOW"

        return {

            "risk_level": risk,

            "items": evidence

        }


    #################
        # =====================================================
    # Build Investigation Story
    # =====================================================

    def build_story(
        self,
        event,
        production,
        reports,
        evidence
    ):

        story = []

        # ----------------------------------------
        # Opening
        # ----------------------------------------

        story.append(

            f"The investigation collected "
            f"{len(evidence['items'])} supporting evidence items."

        )

        story.append(

            f"The overall operational risk level "
            f"was assessed as "
            f"{evidence['risk_level']}."

        )

        # ----------------------------------------
        # Event
        # ----------------------------------------

        if event.get("event_type", "") != "":

            story.append(

                f"The primary incident was identified as "
                f"{event['event_type']}."

            )

        # ----------------------------------------
        # Production
        # ----------------------------------------

        total_coils = len(production)

        total_tons = round(
            production["ACTUAL_TONNAGE"].sum(),
            2
        )

        story.append(

            f"The investigation covered "
            f"{total_coils} coils representing "
            f"{total_tons} tons of production."

        )

        # ----------------------------------------
        # Root Cause
        # ----------------------------------------

        if event.get("root_cause", "") != "":

            story.append(

                f"The probable root cause was "
                f"{event['root_cause']}."

            )

        # ----------------------------------------
        # Impact
        # ----------------------------------------

        if event.get("production_impact", "") != "":

            story.append(

                f"Production impact reported was "
                f"{event['production_impact']}."

            )

        # ----------------------------------------
        # Downtime
        # ----------------------------------------

        duration = event.get(
            "duration_minutes",
            0
        )

        story.append(

            f"The production interruption "
            f"lasted approximately "
            f"{duration} minutes."

        )

        # ----------------------------------------
        # Operator Observation
        # ----------------------------------------

        if len(reports) > 0:

            remarks = reports["Operator Remarks"] \
                .dropna() \
                .astype(str)

            if len(remarks) > 0:

                story.append(

                    f"Operator observations indicate: "
                    f"'{remarks.iloc[0]}'."

                )

        # ----------------------------------------
        # Evidence Count
        # ----------------------------------------

        story.append(

            f"The investigation collected "
            f"{len(evidence)} supporting evidence items."

        )

        # ----------------------------------------
        # Final Assessment
        # ----------------------------------------

        severity = event.get(
            "severity",
            "Unknown"
        )

        confidence = round(
            event.get("confidence", 0) * 100,
            1
        )

        story.append(

            f"Overall assessment indicates a "
            f"{severity} severity operational event "
            f"with AI confidence of "
            f"{confidence}%."

        )

        return "\n\n".join(story)

    ##################
        # =====================================================
    # Main Investigation
    # =====================================================

    def investigate(self, operations):

        # ---------------------------------------
        # Find Major Event
        # ---------------------------------------

        # ---------------------------------------
# Rank Equipment Events
# ---------------------------------------

        suspects = self.rank_equipment_events(operations)
    
        if len(suspects) == 0:

            return {

                "suspects": [],

                "incident": None,

                "summary": {},

                "timeline": [],
        
                "window": {},

                "production_timeline": {},

                "transitions": {},

                "evidence": {

                    "risk_level": "LOW",

                    "items": []

                },

                "story": "No equipment related downtime found.",

                "ai_story": "No equipment related downtime found."

            }

# ---------------------------------------
# Select Highest Ranked Suspect
# ---------------------------------------

        suspect = suspects[0]

        event = suspect["event"]
        # ---------------------------------------
# Build Investigation Window
# ---------------------------------------

        window = self.build_investigation_window(suspect)

        # ---------------------------------------
        # Load Shift Reports
        # ---------------------------------------

        reports = self.get_shift_window(event)

        # ---------------------------------------
        # Load Production Window
        # ---------------------------------------

        production = self.get_production_window(window)
        timeline_data = self.split_production_timeline(

            production,

            window

        )
        transitions = self.detect_transitions(

            timeline_data

        )

        context = self.build_investigation_context(

            suspect,

            window,

            timeline_data,

            transitions,

            reports

        )

        ai_story = self.ai_reasoning(context)

        print("=" * 60)
        print("CRIME SCENE")
        print("=" * 60)
        print(f"Equipment : {window['equipment']}")
        print(f"Event     : {window['event_type']}")
        print(f"Window    : {window['before_start']} --> {window['after_end']}")
        print()

        print(f"Before Incident : {len(timeline_data['before'])} coils")
        print(f"During Incident : {len(timeline_data['during'])} coils")
        print(f"After Recovery  : {len(timeline_data['after'])} coils")

        print("=" * 60)

        print("\nTRANSITIONS")

        for attribute, values in transitions.items():

            print("-" * 40)

            print(attribute)

            print("Before")

            print(values["before"])

            print("After")

            print(values["after"])

        

        # ---------------------------------------
        # Build Timeline
        # ---------------------------------------

        timeline = self.build_timeline(

            event,

            production,

            reports

        )

        # ---------------------------------------
        # Build Evidence
        # ---------------------------------------

        evidence = self.build_evidence(

            event,

            production,

            reports

        )

        # ---------------------------------------
        # Build Story
        # ---------------------------------------

        story = self.build_story(

            event,

            production,

            reports,

            evidence

        )

        # ---------------------------------------
        # Investigation Summary
        # ---------------------------------------

        summary = {

            "event_type":
                event.get(
                    "event_type",
                    ""
                ),

            "severity":
                event.get(
                    "severity",
                    ""
                ),

            "duration_minutes":
                event.get(
                    "duration_minutes",
                    0
                ),

            "confidence":
                event.get(
                    "confidence",
                    0
                )

        }

        # ---------------------------------------
        # Final Result
        # ---------------------------------------

        return {

            "suspects": suspects,
            "window": window,
            "production_timeline": timeline_data,
            "transitions": transitions,
            "ai_story": ai_story,

            "incident": event,

            "summary": summary,

            "timeline": timeline,

            "evidence": evidence,

            "story": story
            
            

        }
