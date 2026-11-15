
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# =====================================
# CONFIGURATION
# =====================================

st.set_page_config(
    page_title="F1 Engineering",
    page_icon="🏎️",
    layout="wide"
)

# =====================================
# DESIGN - BLACK / RED / WHITE
# =====================================

st.markdown("""
<style>

.stApp {
    background-color: #0B0D12;
    color: #FFFFFF;
}

h1, h2, h3, h4, p, label,
.stMarkdown, .stCaption {
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"] {
    background-color: #191D26;
}

section[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

[data-testid="stMetric"] {
    background-color: #191D26;
    border: 1px solid #333946;
    border-left: 4px solid #E10600;
    padding: 18px;
    border-radius: 10px;
}

[data-testid="stMetricLabel"] {
    color: #C7CDD8 !important;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
}

[data-baseweb="select"] > div {
    background-color: #191D26;
    color: white;
    border-color: #555D6B;
}

.stDataFrame {
    color: white;
}

hr {
    border-color: #343A46;
}

</style>
""", unsafe_allow_html=True)


# =====================================
# SIMULATED TELEMETRY DATA
# =====================================

def generate_telemetry(driver):

    distance = np.linspace(0, 5000, 250)

    driver_factor = {
        "VER": 1.00,
        "HAM": 0.97,
        "LEC": 1.02
    }

    factor = driver_factor[driver]

    speed = (
        190
        + 55 * np.sin(2 * np.pi * distance / 5000)
        + 18 * np.sin(6 * np.pi * distance / 5000)
    ) * factor

    braking_zones = [1100, 2700, 4100]

    brake = np.zeros(len(distance))

    for zone in braking_zones:
        brake += 85 * np.exp(
            -((distance - zone) / 110) ** 2
        )

    brake = np.clip(brake, 0, 100)

    throttle = np.clip(
        100 - brake * 1.1,
        0,
        100
    )

    speed = np.clip(speed - brake * 0.7, 60, 340)

    return pd.DataFrame({
        "Distance": distance,
        "Speed": speed,
        "Throttle": throttle,
        "Brake": brake
    })


# =====================================
# SIDEBAR
# =====================================

st.sidebar.title("🏎️ F1 ENGINEERING")
st.sidebar.caption("TELEMETRY SYSTEM")

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Dashboard",
        "Lap Analysis",
        "Driver Comparison",
        "Telemetry"
    ]
)

st.sidebar.divider()

driver = st.sidebar.selectbox(
    "SELECT DRIVER",
    ["VER", "HAM", "LEC"]
)

st.sidebar.caption("F1 TELEMETRY ANALYZER")
st.sidebar.caption("VERSION 3.0")


# =====================================
# SAMPLE LAP DATA
# =====================================

drivers = {
    "VER": [91.2, 90.8, 91.5, 90.5, 91.0],
    "HAM": [92.1, 91.8, 91.2, 91.5, 91.7],
    "LEC": [91.5, 90.9, 91.1, 90.7, 90.8]
}

laps = drivers[driver]


# =====================================
# CHART STYLE
# =====================================

def style_chart(fig, title):

    fig.update_layout(
        title=title,
        template="plotly_dark",
        paper_bgcolor="#0B0D12",
        plot_bgcolor="#191D26",
        font=dict(
            color="#FFFFFF",
            size=13
        ),
        xaxis=dict(
            gridcolor="#343A46",
            zerolinecolor="#555D6B"
        ),
        yaxis=dict(
            gridcolor="#343A46",
            zerolinecolor="#555D6B"
        ),
        legend=dict(
            font=dict(color="white")
        ),
        margin=dict(l=20, r=20, t=60, b=30)
    )

    return fig


# =====================================
# DASHBOARD
# =====================================

if page == "Dashboard":

    st.title("RACE PERFORMANCE")
    st.caption("ENGINEERING OVERVIEW")

    col1, col2, col3 = st.columns(3)

    col1.metric("DRIVER", driver)

    col2.metric(
        "BEST LAP",
        f"{min(laps):.3f} s"
    )

    col3.metric(
        "AVERAGE LAP",
        f"{np.mean(laps):.3f} s"
    )

    df = pd.DataFrame({
        "Lap": range(1, 6),
        "Lap Time": laps
    })

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Lap"],
        y=df["Lap Time"],
        mode="lines+markers",
        name=driver,
        line=dict(color="#E10600", width=3)
    ))

    fig = style_chart(fig, "LAP TIME EVOLUTION")

    st.plotly_chart(fig, use_container_width=True)


# =====================================
# LAP ANALYSIS
# =====================================

elif page == "Lap Analysis":

    st.title("LAP ANALYSIS")

    df = pd.DataFrame({
        "Lap": range(1, 6),
        "Lap Time": laps
    })

    st.metric(
        "BEST LAP",
        f"{df['Lap Time'].min():.3f} s"
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["Lap"],
        y=df["Lap Time"],
        marker_color="#E10600"
    ))

    fig = style_chart(fig, "LAP TIME ANALYSIS")

    st.plotly_chart(fig, use_container_width=True)


# =====================================
# DRIVER COMPARISON
# =====================================

elif page == "Driver Comparison":

    st.title("DRIVER COMPARISON")

    df = pd.DataFrame(drivers)

    fig = go.Figure()

    driver_colors = {
        "VER": "#3671C6",
        "HAM": "#27F4D2",
        "LEC": "#E10600"
    }

    for name in drivers:

        fig.add_trace(go.Scatter(
            x=list(range(1, 6)),
            y=drivers[name],
            mode="lines+markers",
            name=name,
            line=dict(
                color=driver_colors[name],
                width=3
            )
        ))

    fig = style_chart(
        fig,
        "DRIVER LAP TIME COMPARISON"
    )

    st.plotly_chart(fig, use_container_width=True)

    results = pd.DataFrame({
        "Driver": list(drivers.keys()),
        "Best Lap": [
            min(v) for v in drivers.values()
        ],
        "Average Lap": [
            np.mean(v) for v in drivers.values()
        ]
    })

    st.dataframe(
        results,
        use_container_width=True,
        hide_index=True
    )


# =====================================
# TELEMETRY
# =====================================

elif page == "Telemetry":

    st.title("TELEMETRY ANALYSIS")
    st.caption("SPEED / THROTTLE / BRAKE")

    telemetry = generate_telemetry(driver)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "MAX SPEED",
        f"{telemetry['Speed'].max():.1f} km/h"
    )

    col2.metric(
        "AVG SPEED",
        f"{telemetry['Speed'].mean():.1f} km/h"
    )

    col3.metric(
        "MAX BRAKING",
        f"{telemetry['Brake'].max():.1f} %"
    )

    # SPEED

    fig_speed = go.Figure()

    fig_speed.add_trace(go.Scatter(
        x=telemetry["Distance"],
        y=telemetry["Speed"],
        mode="lines",
        name="Speed",
        line=dict(color="#E10600", width=3),
        fill="tozeroy",
        fillcolor="rgba(225,6,0,0.10)"
    ))

    fig_speed.update_yaxes(
        title="Speed (km/h)"
    )

    fig_speed.update_xaxes(
        title="Distance (m)"
    )

    fig_speed = style_chart(
        fig_speed,
        "VEHICLE SPEED"
    )

    st.plotly_chart(
        fig_speed,
        use_container_width=True
    )

    # THROTTLE

    fig_throttle = go.Figure()

    fig_throttle.add_trace(go.Scatter(
        x=telemetry["Distance"],
        y=telemetry["Throttle"],
        mode="lines",
        name="Throttle",
        line=dict(color="#27F4D2", width=3)
    ))

    fig_throttle.update_yaxes(
        title="Throttle (%)",
        range=[0, 105]
    )

    fig_throttle.update_xaxes(
        title="Distance (m)"
    )

    fig_throttle = style_chart(
        fig_throttle,
        "THROTTLE POSITION"
    )

    st.plotly_chart(
        fig_throttle,
        use_container_width=True
    )

    # BRAKE

    fig_brake = go.Figure()

    fig_brake.add_trace(go.Scatter(
        x=telemetry["Distance"],
        y=telemetry["Brake"],
        mode="lines",
        name="Brake",
        line=dict(color="#FFB800", width=3),
        fill="tozeroy",
        fillcolor="rgba(255,184,0,0.10)"
    ))

    fig_brake.update_yaxes(
        title="Brake (%)",
        range=[0, 105]
    )

    fig_brake.update_xaxes(
        title="Distance (m)"
    )

    fig_brake = style_chart(
        fig_brake,
        "BRAKE PRESSURE"
    )

    st.plotly_chart(
        fig_brake,
        use_container_width=True
    )

    st.subheader("TELEMETRY DATA")

    st.dataframe(
        telemetry.round(2),
        use_container_width=True,
        hide_index=True
    )
