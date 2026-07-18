from collections import Counter


class OperationsCorrelationAgent:

    def investigate(
        self,
        downtime_result,
        production_loss_result,
        operator_result
    ):

        # -----------------------------
        # Downtime
        # -----------------------------
        downtime = downtime_result["investigation"]

        critical_equipment = max(
            downtime["downtime_by_equipment"],
            key=downtime["downtime_by_equipment"].get
        )

        critical_shift = max(
            downtime["downtime_by_shift"],
            key=downtime["downtime_by_shift"].get
        )

        # -----------------------------
        # Production Loss
        # -----------------------------
        highest_loss_equipment = max(
            production_loss_result["loss_by_equipment"],
            key=production_loss_result["loss_by_equipment"].get
        )

        total_loss = production_loss_result["total_loss_tonnes"]

        # -----------------------------
        # LLM Events
        # -----------------------------
        events = operator_result["events"]

        issue_counter = Counter()
        severity_counter = Counter()
        impact_counter = Counter()

        root_causes = []

        for e in events:

            issue_counter[e.get("issue_category", "Unknown")] += 1
            severity_counter[e.get("severity", "Unknown")] += 1
            impact_counter[e.get("production_impact", "Unknown")] += 1

            if e.get("root_cause"):
                root_causes.append(e["root_cause"])

        # -----------------------------
        # Findings
        # -----------------------------
        findings = []

        findings.append(
            f"{critical_equipment} recorded the highest downtime."
        )

        findings.append(
            f"{highest_loss_equipment} caused the highest production loss."
        )

        findings.append(
            f"{critical_shift} shift experienced the highest downtime."
        )

        if issue_counter:
            findings.append(
                f"Most frequent issue category was {issue_counter.most_common(1)[0][0]}."
            )

        if severity_counter:
            findings.append(
                f"Most incidents were classified as {severity_counter.most_common(1)[0][0]} severity."
            )

        if impact_counter:
            findings.append(
                f"Majority of events had {impact_counter.most_common(1)[0][0]} production impact."
            )

        # -----------------------------
        # Evidence
        # -----------------------------
        evidence = [

            {
                "type": "Downtime",
                "fact": f"{critical_equipment} highest downtime"
            },

            {
                "type": "Production Loss",
                "fact": f"{highest_loss_equipment} highest production loss"
            },

            {
                "type": "Shift",
                "fact": f"{critical_shift} shift affected most"
            }

        ]

        return {

            "critical_equipment": critical_equipment,

            "critical_shift": critical_shift,

            "total_loss_tonnes": total_loss,

            "issue_distribution": dict(issue_counter),

            "severity_distribution": dict(severity_counter),

            "impact_distribution": dict(impact_counter),

            "root_causes": list(set(root_causes)),

            "findings": findings,

            "evidence": evidence

        }
