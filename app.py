# app.py

import streamlit as st
import plotly.express as px

from reference_agent import ReferenceAgent
from week_agent import WeekAgent
from day_agent import DayAgent
from shift_agent import ShiftAgent
from executive_summary_agent import ExecutiveSummaryAgent


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
    # Executive Context
    # ------------------------------------------

    st.header("Executive Context")

    reference = ReferenceAgent()

    ref = reference.investigate()

    chart = ref["summary"].copy()

    fig = px.line(
        chart,
        x="WEEK_NO",
        y=["PLAN_TONNAGE", "ACTUAL_TONNAGE"],
        markers=True,
        title="12 Week Production Trend"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.text(ref["reference"])

    # ------------------------------------------
    # Weeks
    # ------------------------------------------

    weeks = 5

    words = question.lower().split()

    for i, word in enumerate(words):
        if word.isdigit():
            weeks = int(word)
            break

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
