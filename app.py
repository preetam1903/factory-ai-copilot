import streamlit as st
import plotly.graph_objects as go

from production_service import ProductionService

from context_agent import ContextAgent
from trend_agent import TrendAgent
from operations_intelligence_agent import OperationsIntelligenceAgent
from crime_scene_agent import CrimeSceneInvestigationAgent



# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="AI Manufacturing Investigation Platform",
    layout="wide"
)

st.title("🏭 AI Manufacturing Investigation Platform")

st.caption(
    "AI powered operational investigation and manufacturing intelligence"
)

# ==========================================================
# QUESTION
# ==========================================================

question = st.text_input(
    "Ask a Manufacturing Question",
    value="Why has production reduced over the last 3 weeks?"
)

# ==========================================================
# START INVESTIGATION
# ==========================================================

if st.button("Start Investigation"):

    service = ProductionService()

    # ---------------------------------------------------------
    # DATA VALIDATION
    # ---------------------------------------------------------

    st.header("Data Validation")

    validation = service.validate_weekly_data()

    st.dataframe(
        validation,
        use_container_width=True
    )

    # ---------------------------------------------------------
    # CONTEXT AGENT
    # ---------------------------------------------------------

    st.markdown("---")

    st.header("Step 1 : Understanding Business Context")

    context_agent = ContextAgent()

    context = context_agent.investigate(question)

    st.success("Business context established")

    st.markdown(f"""
### Business Question

{context["business_question"]}

### Objective

{context["objective"]}

### Trend Window

{context["trend_window"]}

### Requested Investigation

{context["requested_window"]}
""")

    # ---------------------------------------------------------
    # TREND AGENT
    # ---------------------------------------------------------

    st.markdown("---")

    st.header("Step 2 : Production Trend Analysis")

    trend_agent = TrendAgent()

    trend = trend_agent.investigate(context)

    st.subheader("Trend Facts (Debug)")

    st.json(trend["trend_facts"])

    st.write("Question Type:", trend["question_type"])
    st.write("Assumption:", trend["assumption"])
    st.write("Assessment:", trend["assessment_status"])
    st.write("Requested Trend:", trend["requested_trend"])
    st.write("Overall Pattern:", trend["overall_pattern"])

    chart = trend["chart"]

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

    recommendation = trend["recommended_window"]

    highlight = chart.tail(
        recommendation["weeks"]
    )

    fig.add_vrect(

        x0=highlight["WEEK_NO"].min()-0.5,

        x1=highlight["WEEK_NO"].max()+0.5,

        fillcolor="yellow",

        opacity=0.15,

        layer="below",

        line_width=0

    )

    fig.update_layout(

        title="Production Trend",

        xaxis_title="Week",

        yaxis_title="Tonnes",

        hovermode="x unified",

        height=450

    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Overall Pattern",
        trend["overall_pattern"]
    )

    c2.metric(
        "Production Loss",
        f'{trend["loss"]:,.0f} t'
    )

    c3.metric(
        "Achievement",
        f'{trend["achievement"]:.1f}%'
    )

    st.info(
        trend["assessment"]
    )

    st.success(
        f"""
AI Recommendation

The production decline started during
{trend["recommended_window"]["label"]}

The investigation should focus on this
window instead of only the user selected period.
"""
    )

     # ---------------------------------------------------------
# OPERATIONS INTELLIGENCE
# ---------------------------------------------------------

    st.markdown("---")

    st.header("Step 3 : Operations Intelligence")

    operations_agent = OperationsIntelligenceAgent()

    operations = operations_agent.investigate(
        trend
    )

    st.success(
        "Operations Intelligence Completed"
    )

    st.dataframe(
        operations["events"],
        use_container_width=True
    )

    # ---------------------------------------------------------
# CRIME SCENE INVESTIGATION
# ---------------------------------------------------------

    st.markdown("---")

    st.header("Step 4 : Crime Scene Investigation")

    crime_agent = CrimeSceneInvestigationAgent()

    crime = crime_agent.investigate(
        operations
    )
    
    st.success(
        "Crime Scene Investigation Completed"
    )

# -----------------------------
# Incident
# -----------------------------

    st.subheader("Incident")

    st.json(
        crime["incident"]
    )

# -----------------------------
# Timeline
# -----------------------------

    st.subheader("Timeline")

    for item in crime["timeline"]:

        st.markdown(
            f"""
    **{item['time']}**

    **{item['title']}**

    {item['description']}
    """
        )

# -----------------------------
# Evidence
# -----------------------------

    st.subheader("Evidence")

    st.success(
        f"Risk Level : {crime['evidence']['risk_level']}"
    )

    for item in crime["evidence"]["items"]:

        st.write("•", item["finding"])

# -----------------------------
# Story
# -----------------------------

    st.subheader("Investigation Story")

    st.info(
        crime["story"]
    )


   
   

    # ---------------------------------------------------------
    # ASK FOLLOW-UP QUESTION
    # ---------------------------------------------------------

    st.markdown("---")

    st.header("Ask a Follow-up Question")

    followup = st.text_input(
        "Continue the investigation",
        placeholder="Why did the finishing mill stop?"
    )

    if followup:

        st.info(
            f"""
Follow-up Question

{followup}

(The conversational investigation agent will use all
previous investigation context instead of starting from
scratch.)
"""
        )

    # ---------------------------------------------------------
    # RAW DATA (OPTIONAL)
    # ---------------------------------------------------------

    with st.expander("View Supporting Data"):

        st.subheader("Production Data")

        st.dataframe(
            service.production,
            use_container_width=True
        )

        st.subheader("Production Plan")

        st.dataframe(
            service.daily_plan,
            use_container_width=True
        )

        st.subheader("Shift Reports")

        st.dataframe(
            service.shift_report,
            use_container_width=True
        )
