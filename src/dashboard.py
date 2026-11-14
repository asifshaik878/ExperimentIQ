
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "outputs" / "experimentiq.db"

st.set_page_config(
    page_title="ExperimentIQ",
    page_icon="📊",
    layout="wide"
)


@st.cache_data
def load_data():
    with sqlite3.connect(DB_PATH) as connection:
        experiments = pd.read_sql_query(
            "SELECT * FROM experiments ORDER BY experiment_id",
            connection
        )

        results = pd.read_sql_query(
            """
            SELECT r.*, m.metric_name, m.metric_key, m.metric_type
            FROM experiment_results r
            LEFT JOIN metric_definitions m
            ON r.metric_definition_id = m.metric_definition_id
            ORDER BY r.experiment_id
            """,
            connection
        )

        variants = pd.read_sql_query(
            """
            SELECT v.*, e.experiment_name
            FROM variants v
            JOIN experiments e
            ON v.experiment_id = e.experiment_id
            """,
            connection
        )

        guardrails = pd.read_sql_query(
            """
            SELECT g.*, m.metric_name
            FROM guardrail_metrics g
            LEFT JOIN metric_definitions m
            ON g.metric_definition_id = m.metric_definition_id
            """,
            connection
        )

        metrics = pd.read_sql_query(
            "SELECT * FROM metric_definitions",
            connection
        )

        audience = pd.read_sql_query(
            """
            SELECT eligibility_status, COUNT(*) AS users
            FROM audience_members
            GROUP BY eligibility_status
            """,
            connection
        )

    return experiments, results, variants, guardrails, metrics, audience


if not DB_PATH.exists():
    st.error(f"Database not found: {DB_PATH}")
    st.stop()

experiments, results, variants, guardrails, metrics, audience = load_data()

st.title("ExperimentIQ")
st.caption(
    "Experimentation analytics platform | Experiment integrity, "
    "treatment effects and operational guardrails"
)

st.sidebar.header("Dashboard Filters")

experiment_options = {
    row["experiment_name"]: row["experiment_id"]
    for _, row in experiments.iterrows()
}

selected_name = st.sidebar.selectbox(
    "Select experiment",
    list(experiment_options.keys())
)

selected_id = experiment_options[selected_name]

selected_experiment = experiments[
    experiments["experiment_id"] == selected_id
].iloc[0]

selected_result = results[
    results["experiment_id"] == selected_id
]

selected_variants = variants[
    variants["experiment_id"] == selected_id
]

selected_guardrails = guardrails[
    guardrails["experiment_id"] == selected_id
]

selected_metrics = metrics[
    metrics["experiment_id"] == selected_id
]

st.sidebar.divider()
st.sidebar.metric("Available experiments", len(experiments))
st.sidebar.metric("Generated users", f"{int(audience['users'].sum()):,}")

total_users = int(audience["users"].sum())
eligible_users = int(
    audience.loc[
        audience["eligibility_status"] == "ELIGIBLE",
        "users"
    ].sum()
)

result = selected_result.iloc[0] if not selected_result.empty else None

st.subheader("Platform Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Experiments", len(experiments))
col2.metric("Total Audience", f"{total_users:,}")
col3.metric("Eligible Users", f"{eligible_users:,}")
col4.metric(
    "Completed Experiments",
    int((experiments["status"] == "COMPLETED").sum())
)

st.divider()

st.subheader("Selected Experiment")

col1, col2, col3 = st.columns(3)

col1.metric("Experiment", selected_name)
col2.metric("Status", selected_experiment["status"])
col3.metric(
    "Outcome Window",
    f"{selected_experiment['outcome_window_days']} days"
)

st.write("**Hypothesis**")
st.write(selected_experiment["hypothesis"])

st.write(
    f"**Experiment ID:** {selected_id}  |  "
    f"**Randomization Unit:** {selected_experiment['randomization_unit']}  |  "
    f"**Seed:** {selected_experiment['random_seed']}"
)

st.divider()

if result is not None:
    st.subheader("Treatment Effect Analysis")

    control_rate = float(result["control_rate"])
    treatment_rate = float(result["treatment_rate"])
    absolute_lift = float(result["absolute_lift"])
    relative_lift = result["relative_lift"]
    p_value = result["p_value"]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Control Conversion", f"{control_rate:.2%}")
    col2.metric("Treatment Conversion", f"{treatment_rate:.2%}")
    col3.metric(
        "Absolute Lift",
        f"{absolute_lift:+.2%}",
        delta=f"{absolute_lift:+.2%}"
    )

    relative_display = (
        f"{float(relative_lift):+.2%}"
        if pd.notna(relative_lift)
        else "N/A"
    )

    col4.metric("Relative Lift", relative_display)

    chart_data = pd.DataFrame({
        "Variant": ["Control", "Treatment"],
        "Conversion Rate": [control_rate, treatment_rate]
    })

    fig = px.bar(
        chart_data,
        x="Variant",
        y="Conversion Rate",
        color="Variant",
        text_auto=".2%",
        title="Control vs Treatment Conversion Rate"
    )

    fig.update_layout(
        yaxis_tickformat=".0%",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Statistical Significance")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "P-value",
        f"{float(p_value):.6f}" if pd.notna(p_value) else "N/A"
    )

    col2.metric(
        "95% Confidence Interval",
        (
            f"[{float(result['confidence_lower']):.4f}, "
            f"{float(result['confidence_upper']):.4f}]"
            if pd.notna(result["confidence_lower"])
            and pd.notna(result["confidence_upper"])
            else "N/A"
        )
    )

    col3.metric(
        "Statistical Significance",
        (
            "Significant"
            if pd.notna(p_value) and float(p_value) < 0.05
            else "Not significant"
            if pd.notna(p_value)
            else "Unavailable"
        )
    )

    st.caption(
        "Statistical significance uses a two-sided 0.05 threshold. "
        "Interpret results alongside experiment integrity and guardrails."
    )

    st.divider()

    st.subheader("Experiment Integrity")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Control Sample",
        f"{int(result['control_sample_size']):,}"
    )

    col2.metric(
        "Treatment Sample",
        f"{int(result['treatment_sample_size']):,}"
    )

    col3.metric(
        "Sample Ratio Mismatch",
        "Detected" if int(result["srm_detected"]) else "Not detected"
    )

    st.write(f"**Analysis Decision:** {result['decision']}")
    st.write(f"**Guardrail Status:** {result['guardrail_status']}")
    st.write(f"**Metric Version:** {result['metric_version']}")

    with st.expander("View analysis plan"):
        st.write(result["analysis_plan"])

st.divider()

st.subheader("Variant Allocation")

if not selected_variants.empty:
    allocation_chart = px.pie(
        selected_variants,
        names="variant_name",
        values="allocation",
        hole=0.45,
        title="Configured Variant Allocation"
    )

    st.plotly_chart(allocation_chart, use_container_width=True)

    st.dataframe(
        selected_variants[
            ["variant_name", "variant_type", "allocation"]
        ],
        use_container_width=True,
        hide_index=True
    )

st.divider()

st.subheader("Guardrail Configuration")

if not selected_guardrails.empty:
    st.dataframe(
        selected_guardrails[
            [
                "guardrail_name",
                "metric_name",
                "threshold",
                "comparison_operator",
                "severity"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No guardrail configurations available.")

st.divider()

st.subheader("Metric Definitions")

st.dataframe(
    selected_metrics[
        [
            "metric_key",
            "metric_name",
            "metric_type",
            "metric_version",
            "effective_from",
            "effective_to",
            "is_primary"
        ]
    ],
    use_container_width=True,
    hide_index=True
)

st.divider()

st.subheader("All Experiment Results")

st.dataframe(
    results[
        [
            "experiment_id",
            "metric_name",
            "control_rate",
            "treatment_rate",
            "absolute_lift",
            "p_value",
            "srm_detected",
            "guardrail_status",
            "decision"
        ]
    ],
    use_container_width=True,
    hide_index=True
)

st.caption(
    "ExperimentIQ | Synthetic experimentation dataset | "
    "Deterministic generation"
)
