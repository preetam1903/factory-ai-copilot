# ==========================================================
# PLANNER AGENT
# ==========================================================

def planner_agent(question: str):
    """
    Decide whether the question is a simple data query
    or a multi-agent investigation.
    """

    q = question.lower()

    plan = {
        "intent": "query",
        "primary_kpi": "Unknown",
        "agents": []
    }

    # -------------------------------
    # Investigation Keywords
    # -------------------------------
    investigation_words = [
        "why",
        "reason",
        "root cause",
        "investigate",
        "analysis",
        "analyse",
        "impact",
        "correlation",
        "anomaly",
        "drop",
        "reduce",
        "decline",
        "increase"
    ]

    # -------------------------------
    # Detect KPI
    # -------------------------------
    if "production" in q:
        plan["primary_kpi"] = "Production"

    elif "dwell" in q:
        plan["primary_kpi"] = "Dwell Time"

    elif "inventory" in q:
        plan["primary_kpi"] = "Inventory"

    elif "active" in q:
        plan["primary_kpi"] = "Active Coils"

    elif "yield" in q:
        plan["primary_kpi"] = "Yield"

    elif "speed" in q:
        plan["primary_kpi"] = "Rolling Speed"

    # -------------------------------
    # Intent
    # -------------------------------
    is_investigation = any(word in q for word in investigation_words)

    if is_investigation:

        plan["intent"] = "investigation"

        plan["agents"] = [
            "Planner Agent",
            "Trend Agent",
            "Event Agent",
            "Inventory Agent",
            "Dwell Agent",
            "Executive Summary Agent"
        ]

    else:

        plan["intent"] = "query"

        plan["agents"] = [
            "Data Query Agent"
        ]

    return plan
