import streamlit as st
import plotly.graph_objects as go

from production_service import ProductionService

from context_agent import ContextAgent
from trend_agent import TrendAgent
from operations_intelligence_agent import OperationsIntelligenceAgent
from crime_scene_agent import CrimeSceneInvestigationAgent
from trend_reasoning_agent import TrendReasoningAgent



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

    #st.header("Data Validation")

    #validation = service.validate_weekly_data()

    #st.dataframe(
        #validation,
        #use_container_width=True
    #)

    # ---------------------------------------------------------
    # CONTEXT AGENT
    # ---------------------------------------------------------

    st.markdown("---")

    st.header("Step 1 : Understanding Business Context")

    context_agent = ContextAgent()

    context = context_agent.investigate(question)
    context["question"] = question

    st.success("Business context established")

    st.markdown("### Investigation Context")

    context_df = pd.DataFrame({
        "Field": [
            "Business Question",
            "Objective",
            "Trend Window",
            "Investigation Window"
        ],
        "Value": [
            context["question"],
            context["objective"],
            context["analysis_window"],
            context["requested_window"]
        ]
    })

    st.table(context_df)

    # ---------------------------------------------------------
    # TREND AGENT
    # ---------------------------------------------------------

    st.markdown("---")

    st.header("Step 2 : Production Trend Investigation")

    trend_agent = TrendAgent()

    trend = trend_agent.investigate(context)

    

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
    
    ############

    st.subheader("1. Investigation Request")

    requested = trend["investigation_period"]
    analysis = trend["analysis_period"]

    c1, c2 = st.columns(2)

    with c1:
        st.info(
        f"""
    **Requested Investigation**

    Weeks **{requested['start_week']} - {requested['end_week']}**

    This is the period requested by the user.
    """
        )

    with c2:
        st.info(
            f"""
    **Analysis Window**

    Weeks **{analysis['start_week']} - {analysis['end_week']}**

    Additional historical weeks are included for trend analysis.
    """
        )

    st.success(
    f"""
    ### Investigation Summary

    **Question**

    {trend["question"]}

    **Investigation Type**

    {trend["question_type"]}

    """
    )

    st.subheader("2. Investigation Assessment")

    if trend["assessment_status"] == "Supported":

        st.success(
            """
    ### Verdict

    ✅ The production data supports the user's assumption.

    The requested production decline has been confirmed.

    Proceed to operational investigation.
    """
        )

    else:

        st.warning(
            """
    ### Verdict

    ⚠ The production data does not support the user's assumption.

    Further operational investigation is currently not justified.
    """
        )



    ##############

    st.subheader("3. Investigation Evidence")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Achievement (Weeks "
        f"{requested['start_week']}-{requested['end_week']})",
        f"{trend['achievement']:.1f}%"
    )

    c2.metric(
        "Production Loss (Weeks "
        f"{requested['start_week']}-{requested['end_week']})",
        f"{trend['loss']:,.0f} t"
    )

    latest = requested["end_week"]

    c3.metric(
        f"Week {latest} vs Week {latest-1}",
        f"{trend['previous_week_change']:.1f}%"
    )

    c4.metric(
        "vs 4-Week Average",
        f"{trend['rolling_average_change']:.1f}%"
    )

    st.markdown("---")

    c5, c6, c7, c8 = st.columns(4)

    c5.metric(
        "Investigation Trend",
        trend["requested_trend"]
    )

    c6.metric(
        "Overall Pattern",
        trend["overall_pattern"]
    )

    c7.metric(
        "Planning Impact",
        trend["planning_impact"]
    )

    c8.metric(
        "Investigation Severity",
        trend["severity"]
    )
    drop = trend["largest_drop"]

    st.info(
        f"📉 Largest production deterioration occurred in Week {drop['week']} ({drop['change']:.1f}%)."
    )
    if trend["recovery_detected"]:

        st.success(
            f"Production recovery detected from Week {trend['recovery_start']}."
        )

    else:

        st.warning(
            "No production recovery detected."
        )

    st.subheader("5. Production Trend Evidence")
    st.plotly_chart(
        fig,
        use_container_width=True
    )

    with st.expander("Investigation Details"):

        st.markdown("### Deterministic Investigation Findings")

        for finding in trend["findings"]:
            st.write("•", finding)

        st.markdown("---")

        st.markdown("### Investigation Facts")

        facts_df = pd.DataFrame(
            trend["trend_facts"].items(),
            columns=["Metric", "Value"]
        )

        st.table(facts_df)


    # ---------------------------------------------------------
# AI Investigation Interpretation
# ---------------------------------------------------------

    st.header("Executive Investigation Report")

    reasoning_agent = TrendReasoningAgent(
        st.secrets["OPENAI_API_KEY"]
    )

    with st.spinner("AI is interpreting investigation findings..."):

        report = reasoning_agent.generate(
            trend["trend_facts"]
        )

    st.markdown(report)

    

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
