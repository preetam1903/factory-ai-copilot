# app.py

import streamlit as st
import plotly.express as px
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
    value="What happened in the last 5 weeks?"
)

if st.button("Investigate"):
    # ------------------------------------------
# Data Validation
# ------------------------------------------

    st.header("🔍 Data Validation")

    service = ProductionService()

    validation = service.validate_weekly_data()

    st.dataframe(validation, use_container_width=True)
    # ------------------------------------------
    # Executive Context
    # ------------------------------------------

    st.header("Executive Context")
   
    weeks = 5

    words = question.lower().split()

    for i, word in enumerate(words):
        if word.isdigit():
            weeks = int(word)
            break

    reference = ReferenceAgent()

    ref = reference.investigate()

    

    chart = ref["summary"].copy()

    fig = go.Figure()

# -----------------------------
# Plan
# -----------------------------
    fig.add_trace(
        go.Scatter(
            x=chart["WEEK_NO"],
            y=chart["PLAN_TONNAGE"],
            mode="lines+markers",
            name="Plan",
            line=dict(width=3)
        )
    )

# -----------------------------
# Actual
# -----------------------------
    fig.add_trace(
        go.Scatter(
            x=chart["WEEK_NO"],
            y=chart["ACTUAL_TONNAGE"],
            mode="lines+markers",
            name="Actual",
            line=dict(width=3)
        )
    )

# -----------------------------
# Highlight Investigation Window
# -----------------------------
    highlight = chart.tail(weeks)

    fig.add_trace(
        go.Scatter(
            x=highlight["WEEK_NO"],
            y=highlight["ACTUAL_TONNAGE"],
            mode="lines+markers",
            name="Investigation",
            line=dict(width=6, color="red"),
            marker=dict(size=12, color="red")
        )
    )

    fig.update_layout(
        title="Production Trend",
        xaxis_title="Week",
        yaxis_title="Tonnes",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.text(ref["reference"])

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
