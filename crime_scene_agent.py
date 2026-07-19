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

            
            "Planned",
            "Planned maintenance",
            "power",
            "electricity",
            "plant shutdown",
            "lunch",
            "break",
            "cleaning",
            "housekeeping",
            "general",
            "safety"

        ]

        equipment_events = []

        for event in events:

            event_type = str(event.get("event_type", "")).strip().lower()

            production_impact = str(
                event.get("production_impact", "")
            ).strip().lower()

    # Skip planned activities
            if (
                event_type == "planned"
                or "planned" in production_impact
            ):
                continue

            equipment_events.append(event)

        # ---------------------------------------
        # Rank by duration
        # ---------------------------------------

        equipment_events = sorted(

            equipment_events,

            key=lambda x: x.get("duration_minutes", 0),

            reverse=True

        )

        print("\n===== RANKED EVENTS =====")

        for e in equipment_events:
            print(
                e["date"],
                e["equipment"],
                e["duration_minutes"],
                e["event_type"]
            )

        print("=========================\n")
    
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

        production = self.service.coil_operation_fact.copy()

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
            production["DATE"].dt.strftime("%Y-%m-%d")
            + " "
            + production["ROLLING_START"].astype(str)
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

    # ---------------------------------------
    # Production Continuity
    # ---------------------------------------

        continuity = {

            "before_coils": len(before),

            "after_coils": len(after),

            "same_grade": False,

            "same_width": False,

            "same_thickness": False,

            "continuity_observation": ""

        }

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

        # ---------------------------------------
# Production Continuity Investigation
# ---------------------------------------

        try:

            if len(before) > 0 and len(after) > 0:

                if "GRADE" in before.columns:

                    continuity["same_grade"] = (

                        before["GRADE"].mode().iloc[0]

                        ==

                        after["GRADE"].mode().iloc[0]

                    )

                if "WIDTH" in before.columns:

                    continuity["same_width"] = (

                        before["WIDTH"].mode().iloc[0]

                        ==

                        after["WIDTH"].mode().iloc[0]

                    )

                if "THICKNESS" in before.columns:

                    continuity["same_thickness"] = (

                        before["THICKNESS"].mode().iloc[0]

                        ==

                        after["THICKNESS"].mode().iloc[0]

                    )

        except Exception:

            pass


# ---------------------------------------
# Engineering Observation
# ---------------------------------------

        if (

            continuity["same_grade"]

            and

            continuity["same_width"]

            and

            continuity["same_thickness"]

        ):

            continuity["continuity_observation"] = (

                "Production resumed with similar dominant product characteristics."

            )

        else:

            continuity["continuity_observation"] = (

                "Production characteristics changed after restart. The available evidence alone cannot determine whether this was due to production scheduling, operational decisions, or normal manufacturing sequence."

            )


        transition["continuity"] = continuity

        return transition

    # =====================================================
# Build Production Narrative
# =====================================================

    def build_production_narrative(self, timeline_data, transitions):

        narrative = []

        before = timeline_data["before"]
        during = timeline_data["during"]
        after = timeline_data["after"]

    # ---------------------------------------
    # Production Quantity
    # ---------------------------------------

        narrative.append(

            f"Production before incident : {len(before)} coils."

        )

        narrative.append(

            f"Production during incident : {len(during)} coils."

        )

        narrative.append(

            f"Production after restart : {len(after)} coils."

        )

    # ---------------------------------------
    # Continuity Observation
    # ---------------------------------------

        continuity = transitions.get("continuity", {})

        observation = continuity.get(

            "continuity_observation",

            "Production continuity could not be determined."

        )

        narrative.append(observation)

    # ---------------------------------------
    # Grade Transition
    # ---------------------------------------

        if "GRADE" in transitions:

            narrative.append(

                f"Grade transition observed : "
                f"{transitions['GRADE']}"

            )

    # ---------------------------------------
    # Width Transition
    # ---------------------------------------

        if "WIDTH" in transitions:

            narrative.append(

                f"Width transition observed : "
                f"{transitions['WIDTH']}"

            )

    # ---------------------------------------
    # Thickness Transition
    # ---------------------------------------

        if "THICKNESS" in transitions:

            narrative.append(

                f"Thickness transition observed : "
                f"{transitions['THICKNESS']}"

            )

        return narrative


    # =====================================================
# Generate Investigation Hypotheses
# =====================================================

    def generate_hypotheses(self, suspect, transitions, reports):

        hypotheses = []

        # Equipment
        hypotheses.append({
            "title": "Equipment related issue",
            "description": "Downtime may have originated from equipment degradation or failure.",
            "supported_by": [],
            "contradicted_by": [],
            "confidence": "Unknown"
        })

        # Production Transition
        hypotheses.append({
            "title": "Production transition",
            "description": "Downtime may be associated with a production changeover.",
            "supported_by": [],
            "contradicted_by": [],
            "confidence": "Unknown"
        })

        # Maintenance
        hypotheses.append({
            "title": "Maintenance activity",
            "description": "Downtime may be related to maintenance execution.",
            "supported_by": [],
            "contradicted_by": [],
            "confidence": "Unknown"
        })

        # Operator
        hypotheses.append({
            "title": "Operational decision",
            "description": "Downtime may have been influenced by operational actions.",
            "supported_by": [],
            "contradicted_by": [],
            "confidence": "Unknown"
        })

        return hypotheses


    # =====================================================
# Build Investigation Context
# =====================================================

    def build_investigation_context(
        self,
        suspect,
        window,
        timeline_data,
        transitions,
        production_narrative,
        hypotheses,
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
            "production_narrative": production_narrative,
            "hypotheses": hypotheses,

            "operator_remarks":
                reports["Operator Remarks"].dropna().tolist()
                if "Operator Remarks" in reports.columns
                else [],

            "investigation_questions": [

                "Could this downtime have been prevented or reduced?",

                "Does the production before and after the downtime support a production scheduling hypothesis?",

                "Did production continue with the same operating conditions after restart?",

                "Do operator remarks support or contradict the production evidence?",

                "What evidence is missing to confirm or reject the leading hypothesis?",

                "What improvements to future shift logs would improve future investigations?"

            ]

        }

    # =====================================================
# AI Crime Scene Reasoning
# =====================================================

    def ai_reasoning(self, context):

        prompt = f"""
You are a Senior Steel Plant Investigation Engineer with more than 25 years of experience in Hot Strip Mill operations.

You are performing a forensic reconstruction of an operational incident.

Your responsibility is NOT to identify a guaranteed root cause.
Review every supplied investigation hypothesis before forming any conclusion.

For each hypothesis explain:

• Evidence supporting it

• Evidence contradicting it

• Evidence still missing

• Diagnostic confidence

• Whether the hypothesis remains active or should be rejected.

Do not jump directly to the final diagnosis.

Your conclusion must be based only on evidence contained in the investigation context.

Your primary responsibility is to investigate whether this downtime could potentially have been prevented or reduced using the available operational evidence.

Think like an experienced manufacturing investigation engineer.

Start with the hypothesis:

"Could this downtime have been avoided?"

Then investigate the evidence before, during and after the incident.

If the available evidence supports the hypothesis, explain why.

If the available evidence contradicts the hypothesis, clearly explain why.

If the available evidence is insufficient, explicitly state that the diagnosis is inconclusive and explain what additional operational data would improve the investigation.

Never guess.
Never overstate certainty.
Support every engineering opinion with available evidence.
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

# 1. Executive Summary

Provide a concise executive summary of the operational incident.

Include:

• Equipment involved

• Downtime duration

• Overall operational impact

• Preliminary engineering assessment

---

# 2. Timeline Reconstruction

Reconstruct the complete sequence of events.

Explain:

• What happened before the incident

• What happened during the incident

• What happened after production restarted

Use both production data and operator observations.

---

# 3. Production Narrative

Review the supplied production narrative.

Explain:

• Production continuity

• Production recovery

• Grade transition

• Width transition

• Thickness transition

Do not infer causes unless supported by evidence.

---

# 4. Investigation Hypotheses

Review EVERY supplied hypothesis individually.

For EACH hypothesis provide:

### Hypothesis

### Evidence Supporting It

### Evidence Contradicting It

### Missing Evidence

### Confidence

High / Medium / Low

### Status

Choose one:

• Active

• Rejected

• Inconclusive

Do not skip any supplied hypothesis.

---

# 5. Overall Evidence Assessment

Summarize the strongest evidence available.

Clearly distinguish:

Evidence supported by production

Evidence supported by operator remarks

Evidence supported by incident history

Evidence that is currently unavailable.

---

# 6. Avoidability Assessment

Determine whether the downtime appears to be:

• Potentially Avoidable

• Potentially Unavoidable

• Inconclusive

Never claim certainty.

Support every conclusion using evidence.

If evidence is insufficient, explicitly state why.

---

# 7. Diagnostic Confidence

Classify overall investigation confidence.

Choose:

• High

• Medium

• Low

Explain why.

Discuss:

• Evidence quality

• Missing operational information

• Reliability of the current investigation.

---

# 8. Recommended Data Improvements

Recommend additional operational information that would improve future investigations.

Examples:

• Detailed shift remarks

• Maintenance findings

• PLC alarms

• Hydraulic pressure

• Rolling force

• Equipment inspection

• Roll condition

• Product transition reason

• Defect observations

Only recommend information that would improve diagnostic confidence.

---

# 9. Executive Conclusion

Provide a balanced engineering conclusion.

Clearly separate:

Established facts

Likely observations

Possible contributing factors

Investigation limitations

Recommended next engineering actions

Do not state any hypothesis as fact unless supported by evidence.
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
        st.subheader("Crime Scene - Ranked Suspects")

        st.json(suspects)
    
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

        st.subheader("DEBUG 1 - Investigation Window")
        st.json(window)

        # ---------------------------------------
        # Load Shift Reports
        # ---------------------------------------

        reports = self.get_shift_window(event)

        # ---------------------------------------
        # Load Production Window
        # ---------------------------------------

        production = self.get_production_window(window)
        st.subheader("COIL DATASET")

        st.write(production.columns.tolist())

        st.dataframe(production.head(10))

        st.subheader("DEBUG 2 - Production Dataset")

        st.write("Rows:", len(production))

        st.write("Columns:")

        st.write(production.columns.tolist())

        st.dataframe(production.head(20))
        
        timeline_data = self.split_production_timeline(

            production,

            window

        )

        st.subheader("DEBUG 3 - Timeline Split")

        st.write("Before:", len(timeline_data["before"]))
        st.write("During:", len(timeline_data["during"]))
        st.write("After:", len(timeline_data["after"]))

        st.write("Before Production")
        st.dataframe(timeline_data["before"])

        st.write("During Production")
        st.dataframe(timeline_data["during"])

        st.write("After Production")
        st.dataframe(timeline_data["after"])
        
        transitions = self.detect_transitions(

            timeline_data

        )

        st.subheader("DEBUG 4 - Detected Transitions")

        st.json(transitions)

        production_narrative = self.build_production_narrative(

            timeline_data,

            transitions

        )
        st.subheader("DEBUG 5 - Production Narrative")

        st.write(production_narrative)

        hypotheses = self.generate_hypotheses(
            suspect,
            transitions,
            reports
        )

        context = self.build_investigation_context(

            suspect,

            window,

            timeline_data,

            transitions,
            production_narrative,
            hypotheses,

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

            if attribute == "continuity":

                print(values)

                continue

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
