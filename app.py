from __future__ import annotations

from pathlib import Path

import fastf1
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from fastf1 import plotting
from plotly.subplots import make_subplots


APP_TITLE = "Formula 1 Telemetry Dashboard"
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)



st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded",
)

fastf1.Cache.enable_cache(str(CACHE_DIR))
plotting.setup_mpl(misc_mpl_mods=False)


@st.cache_data(show_spinner=False)
def get_event_schedule(year: int) -> pd.DataFrame:
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    return schedule[["RoundNumber", "EventName", "Country", "Location", "EventDate"]].dropna(
        subset=["EventName"]
    )


@st.cache_resource(show_spinner=False)
def load_session(year: int, event_name: str, session_name: str):
    session = fastf1.get_session(year, event_name, session_name)
    session.load(weather=False, messages=False)
    return session


def normalize_driver_code(driver: str) -> str:
    return driver.split(" - ", 1)[0].strip()


def available_drivers(session) -> list[str]:
    drivers = []
    for driver_number in session.drivers:
        try:
            info = session.get_driver(driver_number)
            code = str(info.get("Abbreviation", driver_number))
            full_name = str(info.get("FullName", "")).strip()
            drivers.append(f"{code} - {full_name}" if full_name else code)
        except Exception:
            drivers.append(str(driver_number))
    return sorted(drivers)


def pick_lap(session, driver_code: str, mode: str, lap_number: int | None):
    laps = session.laps.pick_drivers(driver_code).pick_quicklaps()
    if laps.empty:
        laps = session.laps.pick_drivers(driver_code)

    if laps.empty:
        return None

    if mode == "Selected lap" and lap_number is not None:
        selected = laps[laps["LapNumber"] == lap_number]
        if not selected.empty:
            return selected.iloc[0]

    return laps.pick_fastest()


def format_timedelta(value) -> str:
    if pd.isna(value):
        return "N/A"
    total_seconds = value.total_seconds()
    minutes = int(total_seconds // 60)
    seconds = total_seconds - minutes * 60
    return f"{minutes}:{seconds:06.3f}"


def telemetry_for_lap(lap) -> pd.DataFrame:
    telemetry = lap.get_telemetry()
    telemetry = telemetry.copy()
    telemetry["Brake"] = telemetry["Brake"].astype(int)
    return telemetry


def build_telemetry_chart(driver_a: str, tel_a: pd.DataFrame, driver_b: str, tel_b: pd.DataFrame | None):
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.035,
        subplot_titles=("Speed", "Throttle", "Brake", "Gear"),
    )

    colors = {"a": "#e10600", "b": "#00a3ff"}

    fig.add_trace(
        go.Scatter(x=tel_a["Distance"], y=tel_a["Speed"], name=f"{driver_a} Speed", line=dict(color=colors["a"])),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=tel_a["Distance"], y=tel_a["Throttle"], name=f"{driver_a} Throttle", line=dict(color=colors["a"])),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=tel_a["Distance"], y=tel_a["Brake"], name=f"{driver_a} Brake", line=dict(color=colors["a"])),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=tel_a["Distance"], y=tel_a["nGear"], name=f"{driver_a} Gear", line=dict(color=colors["a"])),
        row=4,
        col=1,
    )

    if tel_b is not None:
        fig.add_trace(
            go.Scatter(x=tel_b["Distance"], y=tel_b["Speed"], name=f"{driver_b} Speed", line=dict(color=colors["b"])),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=tel_b["Distance"],
                y=tel_b["Throttle"],
                name=f"{driver_b} Throttle",
                line=dict(color=colors["b"]),
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=tel_b["Distance"], y=tel_b["Brake"], name=f"{driver_b} Brake", line=dict(color=colors["b"])),
            row=3,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=tel_b["Distance"], y=tel_b["nGear"], name=f"{driver_b} Gear", line=dict(color=colors["b"])),
            row=4,
            col=1,
        )

    fig.update_yaxes(title_text="km/h", row=1, col=1)
    fig.update_yaxes(title_text="%", row=2, col=1)
    fig.update_yaxes(title_text="On/Off", row=3, col=1, range=[-0.1, 1.1])
    fig.update_yaxes(title_text="Gear", row=4, col=1)
    fig.update_xaxes(title_text="Distance (m)", row=4, col=1)
    fig.update_layout(
        height=860,
        legend_orientation="h",
        margin=dict(l=30, r=30, t=55, b=30),
        hovermode="x unified",
    )
    return fig


def build_track_map(driver_a: str, tel_a: pd.DataFrame, driver_b: str, tel_b: pd.DataFrame | None):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=tel_a["X"],
            y=tel_a["Y"],
            mode="lines",
            name=driver_a,
            line=dict(color="#e10600", width=4),
        )
    )
    if tel_b is not None:
        fig.add_trace(
            go.Scatter(
                x=tel_b["X"],
                y=tel_b["Y"],
                mode="lines",
                name=driver_b,
                line=dict(color="#00a3ff", width=4),
            )
        )
    fig.update_layout(
        height=520,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(visible=False, scaleanchor="y"),
        yaxis=dict(visible=False),
        showlegend=True,
    )
    return fig


def lap_summary(label: str, lap) -> dict[str, str]:
    return {
        "Driver": label,
        "Lap": str(int(lap["LapNumber"])) if not pd.isna(lap["LapNumber"]) else "N/A",
        "Lap time": format_timedelta(lap["LapTime"]),
        "Sector 1": format_timedelta(lap["Sector1Time"]),
        "Sector 2": format_timedelta(lap["Sector2Time"]),
        "Sector 3": format_timedelta(lap["Sector3Time"]),
        "Compound": str(lap.get("Compound", "N/A")),
        "Tyre life": str(int(lap["TyreLife"])) if not pd.isna(lap.get("TyreLife")) else "N/A",
    }


st.title(APP_TITLE)
st.caption("An unofficial FastF1-powered dashboard for comparing Formula 1 lap telemetry.")

with st.sidebar:
    st.header("Session")
    year = st.number_input("Season", min_value=2018, max_value=2026, value=2024, step=1)

    try:
        schedule = get_event_schedule(int(year))
        event_names = schedule["EventName"].tolist()
    except Exception as exc:
        st.error(f"Could not load the {year} calendar. {exc}")
        st.stop()

    event_name = st.selectbox("Grand Prix", event_names, index=max(0, len(event_names) - 1))
    session_name = st.selectbox("Session", ["FP1", "FP2", "FP3", "Q", "SQ", "S", "R"], index=3)
    compare_enabled = st.toggle("Compare two drivers", value=True)
    lap_mode = st.radio("Lap mode", ["Fastest lap", "Selected lap"], horizontal=True)

with st.spinner("Loading session data from FastF1..."):
    try:
        session = load_session(int(year), event_name, session_name)
    except Exception as exc:
        st.error(
            "Could not load this session. Try another race/session, or check your internet connection "
            f"the first time data is downloaded. Details: {exc}"
        )
        st.stop()

drivers = available_drivers(session)
if not drivers:
    st.error("No drivers were found for this session.")
    st.stop()

with st.sidebar:
    driver_a_label = st.selectbox("Driver A", drivers, index=0)
    driver_b_default = 1 if len(drivers) > 1 else 0
    driver_b_label = st.selectbox("Driver B", drivers, index=driver_b_default, disabled=not compare_enabled)

driver_a = normalize_driver_code(driver_a_label)
driver_b = normalize_driver_code(driver_b_label)

lap_number_a = None
lap_number_b = None
if lap_mode == "Selected lap":
    laps_a = session.laps.pick_drivers(driver_a)["LapNumber"].dropna().astype(int).tolist()
    laps_b = session.laps.pick_drivers(driver_b)["LapNumber"].dropna().astype(int).tolist()
    with st.sidebar:
        lap_number_a = st.selectbox("Driver A lap", laps_a, index=len(laps_a) - 1 if laps_a else 0)
        if compare_enabled:
            lap_number_b = st.selectbox("Driver B lap", laps_b, index=len(laps_b) - 1 if laps_b else 0)

lap_a = pick_lap(session, driver_a, lap_mode, lap_number_a)
lap_b = pick_lap(session, driver_b, lap_mode, lap_number_b) if compare_enabled else None

if lap_a is None:
    st.error(f"No usable laps were found for {driver_a}.")
    st.stop()
if compare_enabled and lap_b is None:
    st.error(f"No usable laps were found for {driver_b}.")
    st.stop()

tel_a = telemetry_for_lap(lap_a)
tel_b = telemetry_for_lap(lap_b) if lap_b is not None else None

event_info = schedule[schedule["EventName"] == event_name].iloc[0]
st.subheader(f"{year} {event_name} - {session_name}")
st.caption(f"{event_info['Location']}, {event_info['Country']}")

summary = [lap_summary(driver_a, lap_a)]
if lap_b is not None:
    summary.append(lap_summary(driver_b, lap_b))

st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

metric_cols = st.columns(4)
metric_cols[0].metric("Driver A top speed", f"{tel_a['Speed'].max():.0f} km/h")
metric_cols[1].metric("Driver A avg throttle", f"{tel_a['Throttle'].mean():.1f}%")
if tel_b is not None:
    delta = lap_b["LapTime"].total_seconds() - lap_a["LapTime"].total_seconds()
    metric_cols[2].metric("Lap delta B vs A", f"{delta:+.3f}s")
    metric_cols[3].metric("Driver B top speed", f"{tel_b['Speed'].max():.0f} km/h")
else:
    metric_cols[2].metric("Lap distance", f"{tel_a['Distance'].max():.0f} m")
    metric_cols[3].metric("Brake samples", f"{tel_a['Brake'].sum():.0f}")

tab_telemetry, tab_map, tab_laps = st.tabs(["Telemetry", "Track map", "Lap table"])

with tab_telemetry:
    st.plotly_chart(build_telemetry_chart(driver_a, tel_a, driver_b, tel_b), use_container_width=True)

with tab_map:
    st.plotly_chart(build_track_map(driver_a, tel_a, driver_b, tel_b), use_container_width=True)

with tab_laps:
    lap_columns = [
        "Driver",
        "LapNumber",
        "LapTime",
        "Sector1Time",
        "Sector2Time",
        "Sector3Time",
        "Compound",
        "TyreLife",
        "FreshTyre",
        "Stint",
    ]
    lap_table = session.laps[lap_columns].copy()
    st.dataframe(lap_table, use_container_width=True, hide_index=True)
