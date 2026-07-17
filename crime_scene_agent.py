# ==========================================================
# CRIME SCENE INVESTIGATION AGENT
# ==========================================================

import pandas as pd
from production_service import ProductionService


class CrimeSceneInvestigationAgent:

    def __init__(self):

        self.service = ProductionService()

    # =====================================================
    # Find Major Event
    # =====================================================

    def get_major_event(self, operations):

        if len(operations["events"]) == 0:
            return None

        # Select longest downtime
        major = max(
            operations["events"],
            key=lambda x: x.get("duration_minutes", 0)
        )

        return major

    # =====================================================
    # Read Production Timeline
    # =====================================================

    def get_production_window(self, event):

        production = self.service.production.copy()

        production["DATE"] = pd.to_datetime(
            production["DATE"]
        )

        event_date = pd.to_datetime(event["date"])

        start = event_date - pd.Timedelta(days=1)
        end = event_date + pd.Timedelta(days=1)

        window = production[
            (production["DATE"] >= start)
            &
            (production["DATE"] <= end)
        ].copy()

        return window

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
                    row.get("REMARKS", "")
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

            remarks = reports["REMARKS"] \
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

            remarks = reports["REMARKS"] \
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

        event = self.get_major_event(operations)

        if event is None:

            return {

                "incident": None,

                "timeline": [],

                "evidence": [],

                "story": "No operational incident found."

            }

        # ---------------------------------------
        # Load Production Window
        # ---------------------------------------

        production = self.get_production_window(event)

        # ---------------------------------------
        # Load Shift Reports
        # ---------------------------------------

        reports = self.get_shift_window(event)

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

            "incident": event,

            "summary": summary,

            "timeline": timeline,

            "evidence": evidence,

            "story": story

        }
