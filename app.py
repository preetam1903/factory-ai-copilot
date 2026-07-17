import streamlit as st
import plotly.graph_objects as go

from reference_agent import ReferenceAgent
from week_agent import WeekAgent
from day_agent import DayAgent
from shift_agent import ShiftAgent
from executive_summary_agent import ExecutiveSummaryAgent
from production_service import ProductionService


st.set_page_config(
    page_title="Production AI Copilot",
    layout="wide"
)

st.title("🏭 Production AI Copilot")

question = st.text_input(
    "Ask a Question",
    value="What happened in the last 2 weeks?"
)

if st.button("Investigate"):

    # ----------------------------------------------------------
    # Data Validation
    # ----------------------------------------------------------

    st.header("🔍 Data Validation")

    service = ProductionService()

    validation = service.validate_weekly_data()

    st.dataframe(
        validation,
        use_container_width=True
    )

    # ----------------------------------------------------------
    # Determine Investigation Window
    # ----------------------------------------------------------

    weeks = 5

    words = question.lower().split()

    for word in words:
        if word.isdigit():
            weeks = int(word)
            break

    # ----------------------------------------------------------
    # Executive Production Reference
    # ----------------------------------------------------------

    st.header("🏭 Executive Production Reference")

    reference = ReferenceAgent()

    ref = reference.investigate(weeks)

    investigation = ref["investigation"]
    summary = ref["summary"]
    performance = ref["performance"]

    chart = ref["chart"].copy()

    # ----------------------------------------------------------
    # Trend Graph
    # ----------------------------------------------------------

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=chart["WEEK_NO"],
            y=chart["PLAN_TONNAGE"],
            mode="lines+markers",
            name="Planned Production",
            line=dict(width=3)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=chart["WEEK_NO"],
            y=chart["ACTUAL_TONNAGE"],
            mode="lines+markers",
            name="Actual Production",
            line=dict(width=3)
        )
    )

    highlight = chart.tail(weeks)

    fig.add_vrect(
        x0=highlight["WEEK_NO"].min() - 0.5,
        x1=highlight["WEEK_NO"].max() + 0.5,
        fillcolor="yellow",
        opacity=0.15,
        layer="below",
        line_width=0
    )

    fig.add_annotation(
        x=highlight["WEEK_NO"].min(),
        y=highlight["ACTUAL_TONNAGE"].max(),
        text="Investigation Starts",
        showarrow=True,
        arrowhead=2
    )

    fig.update_layout(
        title="Production Performance Trend",
        xaxis_title="Production Week",
        yaxis_title="Tonnes",
        hovermode="x unified",
        height=450
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ----------------------------------------------------------
    # Investigation Overview
    # ----------------------------------------------------------

    st.markdown("---")

    st.subheader("📋 Investigation Overview")

    st.markdown(f"""
**Business Question**

{investigation["business_question"]}

**Trend Analysis Window**

{investigation["trend_window"]}

This period provides the historical production context used for trend analysis.

**Investigation Window**

{investigation["investigation_window"]}

This is the period selected for detailed investigation.

**Purpose**

{investigation["purpose"]}
""")

    # ----------------------------------------------------------
    # Production Performance Summary
    # ----------------------------------------------------------

    st.markdown("---")

    st.subheader("📊 Production Performance Comparison")

    comparison = {
        "KPI": [
            "Planned Production",
            "Actual Production",
            "Production Loss",
            "Achievement"
        ],
        investigation["trend_window"]: [
            f"{summary['trend']['planned']:,.0f} t",
            f"{summary['trend']['actual']:,.0f} t",
            f"{summary['trend']['loss']:,.0f} t",
            f"{summary['trend']['achievement']:.1f}%"
        ],
        investigation["investigation_window"]: [
            f"{summary['investigation']['planned']:,.0f} t",
            f"{summary['investigation']['actual']:,.0f} t",
            f"{summary['investigation']['loss']:,.0f} t",
            f"{summary['investigation']['achievement']:.1f}%"
        ]
    }

    st.table(comparison)
    # ----------------------------------------------------------
    # Performance Overview
    # ----------------------------------------------------------

    st.markdown("---")

    st.subheader("📈 Performance Overview")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Best Performing Week",
        f"Week {performance['best_week']}",
        f"{performance['best_actual']:,.0f} t"
    )

    c2.metric(
        "Lowest Performing Week",
        f"Week {performance['worst_week']}",
        f"{performance['worst_actual']:,.0f} t"
    )

    c3.metric(
        "Overall Trend",
        performance["trend"]
    )

    # ----------------------------------------------------------
    # AI Production Assessment
    # ----------------------------------------------------------

    st.markdown("---")

    st.subheader("🤖 AI Production Assessment")

    st.info(
        ref["assessment"]
    )

    # ----------------------------------------------------------
    # AI Investigation Roadmap
    # ----------------------------------------------------------

    st.markdown("---")

    st.subheader("🛣️ AI Investigation Roadmap")

    st.markdown(
        "The AI will now perform the following investigations:"
    )

    for item in ref["roadmap"]:
        st.markdown(f"✅ {item}")

    st.success(
        f"""
The Executive Production Reference has established the historical context.

The detailed investigation will now focus on **{investigation['investigation_window']}**.

Proceeding to Weekly Production Analysis...
"""
    )

    # ------------------------------------------
    # Weeks
    # ------------------------------------------

    

    st.header("Week Investigation")

    week_agent = WeekAgent()

    week = week_agent.investigate(weeks)

    st.dataframe(
        week["weekly_summary"],
        use_container_width=True
    )

    st.success(
        f"Worst Week : {week['worst_week']} | Loss : {week['worst_week_loss']:,.0f} tonnes"
    )

    # ------------------------------------------
    # Day
    # ------------------------------------------

    st.header("Day Investigation")

    day_agent = DayAgent()

    day = day_agent.investigate(
        week["worst_week"]
    )

    st.dataframe(
        day["daily_summary"],
        use_container_width=True
    )

    st.success(
        f"Worst Day : {day['worst_day'].date()} | Loss : {day['loss']:,.0f} tonnes"
    )

    # ------------------------------------------
    # Shift
    # ------------------------------------------

    st.header("Shift Investigation")

    shift_agent = ShiftAgent()

    shift = shift_agent.investigate(
        day["worst_day"]
    )

    st.dataframe(
        shift["shift_summary"],
        use_container_width=True
    )

    st.success(
        f"Worst Shift : {shift['worst_shift']} | Loss : {shift['loss']:,.0f} tonnes"
    )

    # ------------------------------------------
    # Shift Reports
    # ------------------------------------------

    st.subheader("Shift Reports")

    st.dataframe(
        shift["reports"],
        use_container_width=True
    )

    # ------------------------------------------
    # Executive Summary
    # ------------------------------------------

    st.header("Executive Summary")

    executive = ExecutiveSummaryAgent()

    result = executive.investigate(weeks)

    st.code(result["summary"])
