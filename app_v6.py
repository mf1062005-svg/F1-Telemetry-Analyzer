"""F1 Telemetry Analyzer V6.1 - Visual Upgrade.

Uses historical OpenF1 CSV exports already created by the user's downloader.
Expected files:
  data/drivers.csv
  data/all_drivers_telemetry.csv (or data/telemetry/*_telemetry.csv)
  data/all_drivers_laps.csv
  data/all_drivers_location.csv (optional; Circuit Map page)

Optional images:
  assets/teams/<team_slug>.png|jpg|webp|svg
  assets/drivers/<DRIVER_CODE>.png|jpg|webp
"""

from __future__ import annotations

from html import escape
from pathlib import Path
import base64
import mimetypes

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# APP CONFIGURATION
# ------------------------------------------------------------
st.set_page_config(
    page_title="F1 Telemetry Analyzer | V6.1",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
ASSETS_DIR = ROOT / "assets"
TEAM_ASSETS_DIR = ASSETS_DIR / "teams"
DRIVER_ASSETS_DIR = ASSETS_DIR / "drivers"

# Session currently used by the user's OpenF1 export.
SESSION_TITLE = "BAHRAIN GRAND PRIX"
SESSION_SUBTITLE = "SAKHIR INTERNATIONAL CIRCUIT  •  QUALIFYING  •  2024"
DATA_SOURCE_LABEL = "OPENF1 HISTORICAL DATA"

# Approximate team palette for the 2024 Bahrain field. If OpenF1 supplies
# team_colour in drivers.csv, that value takes priority.
TEAM_CONFIG = [
    {"slug": "red_bull", "aliases": ("red bull",), "name": "Red Bull Racing", "short": "RB", "color": "#3671C6"},
    {"slug": "ferrari", "aliases": ("ferrari",), "name": "Scuderia Ferrari", "short": "SF", "color": "#E8002D"},
    {"slug": "mercedes", "aliases": ("mercedes",), "name": "Mercedes", "short": "AMG", "color": "#27F4D2"},
    {"slug": "mclaren", "aliases": ("mclaren",), "name": "McLaren", "short": "MCL", "color": "#FF8000"},
    {"slug": "aston_martin", "aliases": ("aston martin",), "name": "Aston Martin", "short": "AM", "color": "#229971"},
    {"slug": "alpine", "aliases": ("alpine",), "name": "Alpine", "short": "ALP", "color": "#FF87BC"},
    {"slug": "williams", "aliases": ("williams",), "name": "Williams", "short": "W", "color": "#64C4FF"},
    {"slug": "visa_rb", "aliases": ("visa cash app", "racing bulls", "rb"), "name": "Visa Cash App RB", "short": "VCARB", "color": "#6692FF"},
    {"slug": "sauber", "aliases": ("sauber", "stake"), "name": "Kick Sauber", "short": "KICK", "color": "#52E252"},
    {"slug": "haas", "aliases": ("haas",), "name": "Haas", "short": "HAAS", "color": "#B6BABD"},
]

CSS = r"""
<style>
:root {
    --bg: #070b12;
    --panel: #101824;
    --panel2: #141f2d;
    --line: #263446;
    --muted: #94a3b8;
    --white: #f5f7fb;
    --red: #e10600;
    --red2: #ff4057;
}
.stApp {
    background:
      radial-gradient(ellipse at 88% 0%, rgba(225,6,0,.13), transparent 31%),
      radial-gradient(ellipse at 5% 34%, rgba(40,90,140,.10), transparent 28%),
      linear-gradient(135deg, #070b12 0%, #0a111b 50%, #080d16 100%);
    color: var(--white);
}
[data-testid="stHeader"] { background: rgba(7,11,18,.88); }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0c1420 0%,#101a28 62%,#0b111b 100%);
    border-right: 1px solid #243247;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.15rem; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { color:#d9e1ec !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] { gap: .18rem; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] {
    background:rgba(255,255,255,.025); padding: .48rem .65rem; border-radius:9px;
    border:1px solid transparent; margin: 1px 0;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
    background:rgba(225,6,0,.13); border-color:rgba(255,64,87,.38);
}
h1,h2,h3,h4,p,label { color:var(--white); }
.block-container { max-width: 1640px; padding-top: 1.45rem; padding-bottom: 2.5rem; }
/* Header hero */
.race-hero {
    position:relative; overflow:hidden; padding:1.45rem 1.65rem 1.35rem;
    border:1px solid #35445a; border-radius:17px; margin-bottom:1.05rem;
    background:
      linear-gradient(110deg,rgba(13,21,33,.98) 0%,rgba(28,24,34,.96) 52%,rgba(13,23,35,.98) 100%);
    box-shadow:0 15px 45px rgba(0,0,0,.22);
}
.race-hero:before {
    content:""; position:absolute; right:-3%; top:-85%; width:40%; height:260%;
    transform:rotate(24deg); background:linear-gradient(90deg,transparent,rgba(225,6,0,.16),transparent);
}
.race-hero:after {
    content:""; position:absolute; right:0; bottom:0; width:29%; height:5px;
    background:linear-gradient(90deg,transparent,#e10600,#ff5263);
}
.hero-eyebrow { color:#ff6872; font-size:.72rem; letter-spacing:.22em; font-weight:800; }
.hero-title { color:#fff; font-size:clamp(1.55rem,3vw,2.6rem); line-height:1.05; font-weight:900; letter-spacing:-.035em; margin:.35rem 0 .45rem; }
.hero-title span { color:#ff4057; }
.hero-sub { color:#aebbd0; font-size:.86rem; letter-spacing:.08em; }
.hero-right { position:absolute; right:1.7rem; top:1.25rem; text-align:right; z-index:1; }
.hero-number { font-size:3rem; line-height:1; font-weight:950; color:rgba(255,255,255,.10); letter-spacing:-.08em; }
.hero-status { display:inline-block; color:#d6e2ef; border:1px solid #40516a; border-radius:999px; padding:.25rem .58rem; font-size:.65rem; letter-spacing:.1em; }
/* Section headers and cards */
.section-kicker { color:#ff6872; font-size:.68rem; font-weight:800; letter-spacing:.18em; text-transform:uppercase; margin-bottom:.12rem; }
.section-title { font-size:1.12rem; font-weight:850; color:#f5f7fb; margin:0 0 .65rem; }
.team-card {
    min-height:140px; padding:13px 13px 11px; border-radius:13px;
    background:linear-gradient(145deg,rgba(22,34,49,.96),rgba(12,19,29,.98));
    border:1px solid #2a394d; border-top:3px solid var(--team-color,#e10600);
    box-shadow:0 6px 18px rgba(0,0,0,.16); text-align:left;
}
.team-mark {
    display:flex; align-items:center; justify-content:center; height:54px; width:100%;
    border-radius:9px; margin-bottom:10px; color:#fff; font-weight:950;
    letter-spacing:.06em; font-size:1.22rem;
    background:linear-gradient(135deg,var(--team-color,#e10600),rgba(10,15,24,.9));
    border:1px solid rgba(255,255,255,.13); text-shadow:0 2px 9px rgba(0,0,0,.42);
}
.team-name { color:#eef3fa; font-size:.83rem; font-weight:800; line-height:1.2; }
.team-meta { color:#93a3b8; font-size:.66rem; margin-top:5px; letter-spacing:.07em; text-transform:uppercase; }
.driver-card {
    background:linear-gradient(145deg,#172333,#0d1521); border:1px solid #2b3a50;
    border-left:3px solid var(--team-color,#e10600); border-radius:12px;
    padding:12px 12px 10px; min-height:90px; margin-bottom:8px;
}
.driver-number { font-size:1.48rem; font-weight:950; line-height:1; color:#fff; }
.driver-code { color:#ff6976; font-weight:900; font-size:.74rem; letter-spacing:.12em; }
.driver-name { color:#eef3fa; font-weight:750; font-size:.83rem; margin-top:5px; }
.driver-team { color:#91a1b5; font-size:.68rem; margin-top:2px; }
.panel-note { color:#91a1b5; font-size:.76rem; }
.pill { display:inline-block; border:1px solid #34455c; border-radius:999px; padding:4px 9px; color:#c7d2e0; font-size:.65rem; letter-spacing:.08em; margin-right:5px; }
/* Metric cards */
[data-testid="stMetric"] {
    background:linear-gradient(145deg,rgba(22,34,49,.98),rgba(12,19,29,.98));
    border:1px solid #2a394d; border-radius:13px; padding:14px 15px;
    box-shadow:0 6px 16px rgba(0,0,0,.14);
}
[data-testid="stMetricLabel"] { color:#9eacc0 !important; font-size:.75rem !important; }
[data-testid="stMetricValue"] { color:#fff !important; font-weight:850 !important; }
[data-testid="stMetricDelta"] { font-size:.72rem !important; }
/* Widgets */
.stButton button, .stDownloadButton button {
    background:linear-gradient(110deg,#c90000,#ee2639); color:#fff; border:0;
    border-radius:9px; font-weight:800; box-shadow:0 5px 16px rgba(225,6,0,.18);
}
.stButton button:hover, .stDownloadButton button:hover { background:#ff4057; color:#fff; border:0; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="textarea"] > div {
    background:#121d2b !important; border-color:#35465e !important;
}
[data-testid="stDataFrame"] { border:1px solid #2b3a50; border-radius:11px; overflow:hidden; }
[data-testid="stExpander"] { background:rgba(18,29,43,.62); border:1px solid #2b3a50; border-radius:10px; }
hr { border-color:#27364a !important; }
footer { visibility:hidden; }
@media (max-width: 800px) {
    .hero-right { display:none; }
    .race-hero { padding:1.15rem; }
    .block-container { padding-left:1rem; padding-right:1rem; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

PLOT_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,24,37,.92)",
    font=dict(color="#e9eff7", family="Arial, sans-serif"),
    margin=dict(l=38, r=24, t=58, b=42),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.12),
    hoverlabel=dict(bgcolor="#152235", bordercolor="#50627b", font_color="#fff"),
)

# ------------------------------------------------------------
# ASSET HELPERS
# ------------------------------------------------------------
def team_config(team_name: str | None) -> dict:
    name = str(team_name or "").lower()
    # Check more specific aliases before short aliases such as "rb".
    for config in TEAM_CONFIG:
        for alias in sorted(config["aliases"], key=len, reverse=True):
            if alias in name:
                return config
    return {"slug": "unknown", "aliases": (), "name": str(team_name or "Unknown team"), "short": "F1", "color": "#8b9bb0"}


def team_color_value(drivers: pd.DataFrame, driver_number: int | float) -> str:
    row = get_driver_row(drivers, driver_number)
    if row is not None and "team_colour" in row.index and pd.notna(row["team_colour"]):
        value = str(row["team_colour"]).strip().replace("#", "")
        if len(value) == 6:
            return f"#{value}"
    if row is not None:
        return team_config(row.get("team_name", ""))["color"]
    return "#ff4057"


def find_team_asset(team_name: str | None) -> Path | None:
    config = team_config(team_name)
    slug = config["slug"]
    if slug == "unknown":
        return None
    for extension in ("png", "webp", "jpg", "jpeg", "svg"):
        candidate = TEAM_ASSETS_DIR / f"{slug}.{extension}"
        if candidate.exists():
            return candidate
    # Also accept common variants users may already have saved.
    aliases = {
        "ferrari": ("ferrari_logo", "scuderia_ferrari"),
        "red_bull": ("redbull", "red_bull_racing"),
        "mercedes": ("mercedes_amg",),
        "mclaren": ("mclaren_f1",),
        "aston_martin": ("astonmartin",),
        "visa_rb": ("rb", "racing_bulls"),
        "sauber": ("kick_sauber",),
    }
    for alias in aliases.get(slug, ()):
        for extension in ("png", "webp", "jpg", "jpeg", "svg"):
            candidate = TEAM_ASSETS_DIR / f"{alias}.{extension}"
            if candidate.exists():
                return candidate
    return None


def find_driver_asset(driver_code: str | None) -> Path | None:
    code = str(driver_code or "").upper()
    if not code:
        return None
    for extension in ("png", "webp", "jpg", "jpeg"):
        candidate = DRIVER_ASSETS_DIR / f"{code}.{extension}"
        if candidate.exists():
            return candidate
    return None


def team_visual(team_name: str, team_colour: str | None = None, width: int = 110):
    config = team_config(team_name)
    color = team_colour or config["color"]
    logo = find_team_asset(team_name)
    if logo:
        st.image(str(logo), width=width)
    else:
        st.markdown(
            f'<div class="team-mark" style="--team-color:{escape(color)}">{escape(config["short"])}</div>',
            unsafe_allow_html=True,
        )


def team_card_html(team_name: str, team_colour: str, driver_count: int) -> str:
    config = team_config(team_name)
    logo = find_team_asset(team_name)
    if logo:
        mime = mimetypes.guess_type(str(logo))[0] or "image/png"
        encoded = base64.b64encode(logo.read_bytes()).decode("ascii")
        visual = (
            f'<img src="data:{mime};base64,{encoded}" '
            'style="max-height:54px;max-width:100%;object-fit:contain" alt="team logo">'
        )
    else:
        visual = f'<div class="team-mark" style="--team-color:{escape(team_colour)}">{escape(config["short"])}</div>'
    return (
        f'<div class="team-card" style="--team-color:{escape(team_colour)}">'
        f'<div style="height:58px;display:flex;align-items:center;justify-content:center;margin-bottom:8px">{visual}</div>'
        f'<div class="team-name">{escape(team_name)}</div>'
        f'<div class="team-meta">{driver_count} DRIVER(S) &bull; {escape(config["short"])}</div>'
        '</div>'
    )

def driver_card_html(row: pd.Series, team_colour: str) -> str:
    code = escape(str(row.get("name_acronym", "---")))
    name = escape(str(row.get("full_name", "Unknown driver")))
    team = escape(str(row.get("team_name", "Unknown team")))
    number = escape(str(int(row["driver_number"])) if pd.notna(row.get("driver_number")) else "—")
    return f"""
    <div class="driver-card" style="--team-color:{escape(team_colour)}">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
        <div class="driver-number">{number}</div><div class="driver-code">{code}</div>
      </div>
      <div class="driver-name">{name}</div>
      <div class="driver-team">{team}</div>
    </div>
    """


def render_driver_identity(row: pd.Series, colour: str):
    code = str(row.get("name_acronym", ""))
    photo = find_driver_asset(code)
    c1, c2 = st.columns([1, 4])
    with c1:
        if photo:
            st.image(str(photo), use_container_width=True)
        else:
            number = row.get("driver_number", "—")
            st.markdown(
                f'<div class="team-mark" style="--team-color:{escape(colour)};height:74px;font-size:1.6rem">{escape(str(int(number)) if pd.notna(number) else "F1")}</div>',
                unsafe_allow_html=True,
            )
    with c2:
        st.markdown(f"### {escape(str(row.get('full_name', code)))}")
        st.markdown(
            f'<span class="pill">{escape(code)}</span><span class="pill">{escape(str(row.get("team_name", "")))}</span>',
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------
# DATA LOADING
# ------------------------------------------------------------
@st.cache_data(show_spinner=False)
def read_csv_cached(path_string: str, modified_time: float) -> pd.DataFrame:
    path = Path(path_string)
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except (pd.errors.ParserError, UnicodeDecodeError, OSError):
        return pd.DataFrame()


def load_csv(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    return read_csv_cached(str(path), path.stat().st_mtime)


def load_telemetry() -> pd.DataFrame:
    combined = load_csv("all_drivers_telemetry.csv")
    if not combined.empty:
        return combined
    folder = DATA_DIR / "telemetry"
    files = list(folder.glob("*_telemetry.csv")) if folder.exists() else []
    frames = []
    for file in files:
        try:
            frame = pd.read_csv(file)
            if not frame.empty:
                frames.append(frame)
        except Exception:
            continue
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def prepare_data():
    drivers = load_csv("drivers.csv")
    telemetry = load_telemetry()
    laps = load_csv("all_drivers_laps.csv")
    location = load_csv("all_drivers_location.csv")

    if not telemetry.empty:
        if "driver_number" in telemetry.columns:
            telemetry["driver_number"] = pd.to_numeric(telemetry["driver_number"], errors="coerce")
        if "date" in telemetry.columns:
            telemetry["date"] = pd.to_datetime(telemetry["date"], utc=True, errors="coerce")
        for column in ["speed", "throttle", "brake", "rpm", "n_gear", "drs"]:
            if column in telemetry.columns:
                telemetry[column] = pd.to_numeric(telemetry[column], errors="coerce")

    if not drivers.empty and "driver_number" in drivers.columns:
        drivers["driver_number"] = pd.to_numeric(drivers["driver_number"], errors="coerce")

    if not laps.empty:
        for column in ["driver_number", "lap_number", "lap_duration"]:
            if column in laps.columns:
                laps[column] = pd.to_numeric(laps[column], errors="coerce")
        if "date_start" in laps.columns:
            laps["date_start"] = pd.to_datetime(laps["date_start"], utc=True, errors="coerce")
        if "is_pit_out_lap" in laps.columns:
            laps = laps[laps["is_pit_out_lap"].fillna(False) == False].copy()  # noqa: E712
        if not drivers.empty and {"driver_number", "name_acronym"}.issubset(drivers.columns):
            mapping = drivers.set_index("driver_number")["name_acronym"].to_dict()
            laps["driver_code"] = laps["driver_number"].map(mapping)

    if not location.empty:
        if "driver_number" in location.columns:
            location["driver_number"] = pd.to_numeric(location["driver_number"], errors="coerce")
        if "date" in location.columns:
            location["date"] = pd.to_datetime(location["date"], utc=True, errors="coerce")
        for column in ["x", "y", "z"]:
            if column in location.columns:
                location[column] = pd.to_numeric(location[column], errors="coerce")

    return drivers, telemetry, laps, location


def driver_label(row) -> str:
    if hasattr(row, "_asdict"):
        row = row._asdict()
    code = row.get("name_acronym", "")
    name = row.get("full_name", "")
    team = row.get("team_name", "")
    return f"{code} — {name} ({team})"


def get_driver_row(drivers: pd.DataFrame, driver_number: int | float):
    if drivers.empty or "driver_number" not in drivers.columns:
        return None
    match = drivers[drivers["driver_number"] == driver_number]
    return None if match.empty else match.iloc[0]


def best_laps_table(laps: pd.DataFrame, drivers: pd.DataFrame) -> pd.DataFrame:
    if laps.empty or "lap_duration" not in laps.columns or "driver_number" not in laps.columns:
        return pd.DataFrame()
    valid = laps.dropna(subset=["lap_duration"]).copy()
    if valid.empty:
        return pd.DataFrame()
    best = valid.sort_values("lap_duration").groupby("driver_number", as_index=False).first().sort_values("lap_duration")
    if not drivers.empty and "driver_number" in drivers.columns:
        lookup = drivers.drop_duplicates("driver_number").set_index("driver_number")
        for col in ["name_acronym", "full_name", "team_name", "team_colour"]:
            if col in lookup.columns:
                best[col] = best["driver_number"].map(lookup[col].to_dict())
    if "name_acronym" not in best.columns and "driver_code" in best.columns:
        best["name_acronym"] = best["driver_code"]
    return best.reset_index(drop=True)


def get_lap_row(laps: pd.DataFrame, driver_number: int | float, lap_number: int):
    if laps.empty or not {"driver_number", "lap_number"}.issubset(laps.columns):
        return None
    subset = laps[(laps["driver_number"] == driver_number) & (laps["lap_number"] == lap_number)]
    return None if subset.empty else subset.sort_values("lap_duration").iloc[0]


def telemetry_for_lap(telemetry: pd.DataFrame, driver_number: int | float, lap_row) -> pd.DataFrame:
    if telemetry.empty or lap_row is None or "date" not in telemetry.columns:
        return pd.DataFrame()
    start = lap_row.get("date_start")
    duration = lap_row.get("lap_duration")
    if pd.isna(start) or pd.isna(duration):
        return pd.DataFrame()
    subset = telemetry[telemetry["driver_number"] == driver_number].copy()
    subset = subset.dropna(subset=["date"])
    if subset.empty:
        return subset
    begin = start - pd.Timedelta(seconds=0.8)
    end = start + pd.Timedelta(seconds=float(duration) + 0.8)
    subset = subset[(subset["date"] >= begin) & (subset["date"] <= end)].copy()
    if subset.empty:
        return subset
    subset = subset.sort_values("date")
    subset["elapsed_s"] = (subset["date"] - start).dt.total_seconds()
    subset["lap_progress"] = np.clip(subset["elapsed_s"] / float(duration) * 100.0, 0, 100)
    return subset


def team_color(drivers: pd.DataFrame, driver_number: int | float) -> str:
    row = get_driver_row(drivers, driver_number)
    if row is not None:
        return team_color_value(drivers, driver_number)
    return "#ff4057"


def format_lap_time(seconds) -> str:
    if pd.isna(seconds):
        return "—"
    minutes = int(float(seconds) // 60)
    remainder = float(seconds) - minutes * 60
    return f"{minutes}:{remainder:06.3f}"


def section_heading(kicker: str, title: str):
    st.markdown(
        f'<div class="section-kicker">{escape(kicker)}</div><div class="section-title">{escape(title)}</div>',
        unsafe_allow_html=True,
    )


def no_data_box(message: str):
    st.markdown(
        f'<div class="team-card"><div class="team-name">DATA NOT AVAILABLE</div><div class="team-meta">{escape(message)}</div></div>',
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------
# LOAD DATA / VALIDATE
# ------------------------------------------------------------
drivers, telemetry, laps, location = prepare_data()

st.markdown(
    f"""
    <div class="race-hero">
      <div class="hero-eyebrow">RACE ENGINEERING  /  TELEMETRY INTELLIGENCE</div>
      <div class="hero-title">F1 TELEMETRY <span>ANALYZER</span></div>
      <div class="hero-sub">{SESSION_TITLE} &nbsp; • &nbsp; {SESSION_SUBTITLE}</div>
      <div style="margin-top:13px"><span class="pill">{DATA_SOURCE_LABEL}</span><span class="pill">VISUAL EDITION 6.1</span><span class="pill">UNOFFICIAL / EDUCATIONAL</span></div>
      <div class="hero-right"><div class="hero-number">06</div><div class="hero-status">ENGINEERING DESK</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

if drivers.empty:
    st.error("Fichier data/drivers.csv introuvable ou vide. Lance d'abord ton script download_openf1_telemetry.py.")
    st.stop()
if telemetry.empty:
    st.error("Aucune télémétrie trouvée. Vérifie data/all_drivers_telemetry.csv ou data/telemetry/.")
    st.stop()
if not {"driver_number", "date"}.issubset(telemetry.columns):
    st.error("Le CSV de télémétrie doit contenir les colonnes driver_number et date.")
    st.stop()
if "driver_number" not in drivers.columns or "name_acronym" not in drivers.columns:
    st.error("drivers.csv doit contenir au minimum driver_number et name_acronym.")
    st.stop()

available_numbers = sorted(int(value) for value in telemetry["driver_number"].dropna().unique())
available_drivers = drivers[drivers["driver_number"].isin(available_numbers)].copy()
available_drivers = available_drivers.sort_values("name_acronym")
if available_drivers.empty:
    st.error("Aucun pilote des fichiers telemetry ne correspond à drivers.csv.")
    st.stop()

labels = {int(row.driver_number): driver_label(row) for row in available_drivers.itertuples(index=False)}
code_by_number = {int(row.driver_number): str(row.name_acronym) for row in available_drivers.itertuples(index=False)}

# ------------------------------------------------------------
# SIDEBAR / NAVIGATION
# ------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
          <div style="width:42px;height:42px;border-radius:11px;background:linear-gradient(135deg,#e10600,#7d1018);display:flex;align-items:center;justify-content:center;font-weight:950;color:#fff;font-size:1.05rem;box-shadow:0 5px 18px #e1060033">F1</div>
          <div><div style="font-size:.88rem;font-weight:950;color:#fff;letter-spacing:.07em">TELEMETRY LAB</div><div style="font-size:.61rem;color:#92a2b7;letter-spacing:.16em">ENGINEERING SOFTWARE</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("VISUAL EDITION • V6.1")
    st.divider()
    page = st.radio(
        "WORKSPACE",
        ["Dashboard", "Telemetry Analysis", "Driver Comparison", "Circuit Map", "Lap Data"],
        index=0,
        format_func=lambda x: {
            "Dashboard": "◈  Command Center",
            "Telemetry Analysis": "⌁  Telemetry Lab",
            "Driver Comparison": "⇄  Driver Battle",
            "Circuit Map": "◎  Circuit Explorer",
            "Lap Data": "▤  Lap & Sector Data",
        }.get(x, x),
    )
    st.divider()
    st.markdown("**ACTIVE SESSION**")
    st.markdown("<span class='pill'>2024</span><span class='pill'>QUALIFYING</span>", unsafe_allow_html=True)
    st.write("🇧🇭 Bahrain • Sakhir")
    st.caption(f"{len(available_drivers)} drivers with telemetry")
    st.divider()
    st.caption("OpenF1 is an independent, unofficial data project. Telemetry and position samples are subject to source availability.")

# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------
if page == "Dashboard":
    best = best_laps_table(laps, drivers)
    total_samples = len(telemetry)
    num_drivers = telemetry["driver_number"].nunique()
    num_laps = len(laps) if not laps.empty else 0
    avg_speed = telemetry["speed"].mean() if "speed" in telemetry.columns else np.nan
    max_speed = telemetry["speed"].max() if "speed" in telemetry.columns else np.nan

    section_heading("SESSION OVERVIEW", "The command center")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("DRIVERS ONLINE", f"{num_drivers}/20")
    c2.metric("TELEMETRY SAMPLES", f"{total_samples:,}".replace(",", " "))
    c3.metric("RECORDED LAPS", f"{num_laps:,}".replace(",", " "))
    c4.metric("AVG SPEED", f"{avg_speed:.1f} km/h" if pd.notna(avg_speed) else "—")
    c5.metric("TOP SPEED", f"{max_speed:.0f} km/h" if pd.notna(max_speed) else "—")

    st.write("")
    section_heading("THE PADDOCK", "2024 team lineup")
    teams = available_drivers[[c for c in ["team_name", "team_colour"] if c in available_drivers.columns]].drop_duplicates("team_name") if "team_name" in available_drivers.columns else pd.DataFrame()
    if not teams.empty:
        team_cols = st.columns(5)
        for idx, (_, team) in enumerate(teams.sort_values("team_name").iterrows()):
            team_name = str(team.get("team_name", "Unknown team"))
            cfg = team_config(team_name)
            color = str(team.get("team_colour", cfg["color"]))
            if not color.startswith("#"):
                color = f"#{color}"
            team_drivers = available_drivers[available_drivers["team_name"] == team_name]
            with team_cols[idx % 5]:
                st.markdown(
                    team_card_html(team_name, color, len(team_drivers)),
                    unsafe_allow_html=True,
                )

    st.write("")
    left, right = st.columns([1.35, 1])
    with left:
        section_heading("TIMING SCREEN", "Fastest recorded laps")
        if not best.empty:
            display = best.copy()
            display.insert(0, "POS", range(1, len(display) + 1))
            display["LAP TIME"] = display["lap_duration"].apply(format_lap_time)
            cols = [c for c in ["POS", "name_acronym", "full_name", "team_name", "LAP TIME", "lap_number", "st_speed"] if c in display.columns]
            st.dataframe(
                display[cols].rename(columns={
                    "name_acronym": "CODE", "full_name": "DRIVER", "team_name": "TEAM",
                    "lap_number": "LAP", "st_speed": "SPEED TRAP",
                }),
                use_container_width=True,
                hide_index=True,
                height=min(480, 38 * (len(display) + 1)),
            )
        else:
            no_data_box("No valid lap timing rows were found in all_drivers_laps.csv.")
    with right:
        section_heading("PACE ANALYSIS", "Top 10 lap times")
        if not best.empty:
            top = best.head(10).copy()
            top["code"] = top.get("name_acronym", top["driver_number"].astype(str))
            fig = px.bar(
                top.sort_values("lap_duration", ascending=True),
                x="lap_duration", y="code", orientation="h",
                color="team_name" if "team_name" in top.columns else None,
                hover_data=[c for c in ["full_name", "lap_number"] if c in top.columns],
                labels={"lap_duration": "Lap time (seconds)", "code": "Driver"},
            )
            fig.update_layout(**PLOT_LAYOUT, showlegend=False, yaxis_title="", xaxis_title="Lap time (s)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Lap chart will appear when lap timing data is available.")

    st.write("")
    section_heading("DRIVER GRID", "The 20-car field")
    grid_cols = st.columns(5)
    for idx, (_, driver) in enumerate(available_drivers.iterrows()):
        colour = team_color_value(drivers, driver["driver_number"])
        with grid_cols[idx % 5]:
            photo = find_driver_asset(driver.get("name_acronym"))
            if photo:
                st.image(str(photo), use_container_width=True)
            st.markdown(driver_card_html(driver, colour), unsafe_allow_html=True)

# ------------------------------------------------------------
# TELEMETRY ANALYSIS
# ------------------------------------------------------------
elif page == "Telemetry Analysis":
    section_heading("TELEMETRY LAB", "Single-driver analysis")
    chosen_number = st.selectbox(
        "Select driver",
        options=[int(x) for x in available_drivers["driver_number"].tolist()],
        format_func=lambda x: labels[x],
    )
    selected_driver = get_driver_row(drivers, chosen_number)
    colour = team_color(drivers, chosen_number)
    if selected_driver is not None:
        render_driver_identity(selected_driver, colour)
    driver_laps = laps[laps["driver_number"] == chosen_number].dropna(subset=["lap_duration"]).copy() if not laps.empty and "lap_duration" in laps.columns else pd.DataFrame()

    if driver_laps.empty:
        st.warning("No valid lap timing rows for this driver. The full-session telemetry can still be inspected below.")
        raw = telemetry[telemetry["driver_number"] == chosen_number].sort_values("date").copy()
        if raw.empty:
            st.stop()
        c1, c2, c3 = st.columns(3)
        if "speed" in raw.columns:
            c1.metric("TOP SPEED", f"{raw['speed'].max():.0f} km/h")
            c2.metric("AVG SPEED", f"{raw['speed'].mean():.1f} km/h")
        if "rpm" in raw.columns:
            c3.metric("MAX RPM", f"{raw['rpm'].max():,.0f}")
        if "date" in raw.columns and "speed" in raw.columns:
            raw["sample_time"] = (raw["date"] - raw["date"].min()).dt.total_seconds()
            fig = px.line(raw, x="sample_time", y="speed", title="Full-session speed trace")
            fig.update_traces(line=dict(color=colour, width=2.4))
            fig.update_layout(**PLOT_LAYOUT, xaxis_title="Session elapsed time (s)", yaxis_title="Speed (km/h)")
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(raw, use_container_width=True, hide_index=True)
        st.stop()

    driver_laps = driver_laps.sort_values("lap_duration")
    lap_numbers = driver_laps["lap_number"].dropna().astype(int).drop_duplicates().tolist()
    selected_lap = st.selectbox(
        "Select lap (fastest first)",
        options=lap_numbers,
        format_func=lambda n: f"Lap {n} — {format_lap_time(driver_laps[driver_laps['lap_number'] == n].iloc[0]['lap_duration'])}",
    )
    lap_row = get_lap_row(laps, chosen_number, selected_lap)
    trace = telemetry_for_lap(telemetry, chosen_number, lap_row)
    if trace.empty:
        st.warning("Not enough telemetry points around this lap timestamp. Try another lap, or use the full-session CSV export.")
        st.stop()

    max_speed = trace["speed"].max() if "speed" in trace.columns else np.nan
    avg_speed_lap = trace["speed"].mean() if "speed" in trace.columns else np.nan
    max_rpm = trace["rpm"].max() if "rpm" in trace.columns else np.nan
    full_throttle = (trace["throttle"] >= 95).mean() * 100 if "throttle" in trace.columns else np.nan
    brake_pct = (trace["brake"] > 0).mean() * 100 if "brake" in trace.columns else np.nan

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("LAP TIME", format_lap_time(lap_row["lap_duration"]))
    m2.metric("TOP SPEED", f"{max_speed:.0f} km/h" if pd.notna(max_speed) else "—")
    m3.metric("AVG SPEED", f"{avg_speed_lap:.1f} km/h" if pd.notna(avg_speed_lap) else "—")
    m4.metric("MAX RPM", f"{max_rpm:,.0f}" if pd.notna(max_rpm) else "—")
    m5.metric("BRAKE ACTIVE", f"{brake_pct:.1f}%" if pd.notna(brake_pct) else "—")

    if "speed" in trace.columns:
        fig = px.area(trace, x="elapsed_s", y="speed", title="Speed trace — lap timeline")
        fig.update_traces(line=dict(color=colour, width=2.5), fillcolor="rgba(225,6,0,.12)")
        fig.update_layout(**PLOT_LAYOUT, xaxis_title="Elapsed time (s)", yaxis_title="Speed (km/h)")
        st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if {"throttle", "brake"}.issubset(trace.columns):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=trace["elapsed_s"], y=trace["throttle"], name="Throttle (%)", line=dict(color="#25d7a0", width=2.2)))
            fig.add_trace(go.Scatter(x=trace["elapsed_s"], y=trace["brake"], name="Brake (0/100)", line=dict(color="#ff5263", width=2), fill="tozeroy", opacity=.45))
            fig.update_layout(title="Throttle & brake", xaxis_title="Elapsed time (s)", yaxis_title="Throttle % / Brake state", yaxis=dict(range=[0, 105]), **PLOT_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
    with col_b:
        if "rpm" in trace.columns:
            fig = px.line(trace, x="elapsed_s", y="rpm", title="Engine RPM")
            fig.update_traces(line=dict(color="#53a9ff", width=2.1))
            fig.update_layout(**PLOT_LAYOUT, xaxis_title="Elapsed time (s)", yaxis_title="RPM")
            st.plotly_chart(fig, use_container_width=True)

    if "n_gear" in trace.columns:
        fig = px.line(trace, x="elapsed_s", y="n_gear", title="Gear selection")
        fig.update_traces(line=dict(color="#f4c95d", shape="hv", width=2.1))
        fig.update_layout(yaxis=dict(dtick=1, range=[0, 9]), xaxis_title="Elapsed time (s)", **PLOT_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    st.download_button(
        "Download selected lap telemetry CSV",
        data=trace.to_csv(index=False).encode("utf-8"),
        file_name=f"{code_by_number.get(chosen_number, chosen_number)}_lap_{selected_lap}_telemetry.csv",
        mime="text/csv",
    )
    with st.expander("View raw lap telemetry"):
        st.dataframe(trace, use_container_width=True, hide_index=True)

# ------------------------------------------------------------
# DRIVER COMPARISON
# ------------------------------------------------------------
elif page == "Driver Comparison":
    section_heading("HEAD-TO-HEAD", "Compare driver pace")
    if laps.empty:
        st.warning("The file all_drivers_laps.csv is required to compare lap traces.")
        st.stop()
    defaults = [int(x) for x in available_drivers["driver_number"].head(2).tolist()]
    selected_numbers = st.multiselect(
        "Choose 2 to 4 drivers",
        options=[int(x) for x in available_drivers["driver_number"].tolist()],
        default=defaults,
        format_func=lambda x: labels[x],
    )
    if len(selected_numbers) < 2:
        st.info("Select at least two drivers.")
        st.stop()
    if len(selected_numbers) > 4:
        st.warning("Select no more than four drivers to keep the chart readable.")
        st.stop()

    fig = go.Figure()
    summary_rows = []
    for number in selected_numbers:
        subset = laps[laps["driver_number"] == number].dropna(subset=["lap_duration"]).sort_values("lap_duration")
        if subset.empty:
            continue
        fastest = subset.iloc[0]
        trace = telemetry_for_lap(telemetry, number, fastest)
        if trace.empty or "speed" not in trace.columns:
            continue
        trace = trace.dropna(subset=["speed"])
        colour = team_color(drivers, number)
        code = code_by_number.get(number, str(number))
        fig.add_trace(go.Scatter(
            x=trace["lap_progress"], y=trace["speed"], mode="lines",
            name=f"{code} — {format_lap_time(fastest['lap_duration'])}",
            line=dict(color=colour, width=2.7),
        ))
        summary_rows.append({
            "Driver": code,
            "Team": str(get_driver_row(drivers, number).get("team_name", "")) if get_driver_row(drivers, number) is not None else "",
            "Best lap": format_lap_time(fastest["lap_duration"]),
            "Lap number": int(fastest["lap_number"]),
            "Top speed (km/h)": round(trace["speed"].max(), 1),
        })

    if not fig.data:
        st.warning("Could not align telemetry around the selected lap timestamps. Check date_start in all_drivers_laps.csv.")
        st.stop()
    fig.update_layout(title="Speed comparison — normalized lap progress", xaxis_title="Lap progress (%)", yaxis_title="Speed (km/h)", **PLOT_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)
    if summary_rows:
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
    st.caption("Laps are aligned by normalized elapsed time (0–100%), not by official track distance. Drivers may have completed their laps under different track and traffic conditions.")

# ------------------------------------------------------------
# CIRCUIT MAP
# ------------------------------------------------------------
elif page == "Circuit Map":
    section_heading("TRACK POSITION", "Circuit explorer")
    if location.empty:
        st.warning("The position file data/all_drivers_location.csv has not been created yet.")
        st.code("python download_track_positions.py", language="bash")
        st.caption("The download script fetches approximate x/y/z car-position samples from OpenF1. These are telemetry coordinates, not a surveyed or official circuit map.")
        st.stop()
    if not {"driver_number", "date", "x", "y"}.issubset(location.columns):
        st.error("all_drivers_location.csv must include driver_number, date, x and y columns.")
        st.stop()

    map_numbers = sorted(int(x) for x in location["driver_number"].dropna().unique())
    map_drivers = available_drivers[available_drivers["driver_number"].isin(map_numbers)]
    if map_drivers.empty:
        st.warning("No available driver has position samples in the location file.")
        st.stop()
    chosen_number = st.selectbox("Select driver for track map", options=[int(x) for x in map_drivers["driver_number"].tolist()], format_func=lambda x: labels.get(x, str(x)))
    driver_laps = laps[laps["driver_number"] == chosen_number].dropna(subset=["lap_duration"]).sort_values("lap_duration") if not laps.empty else pd.DataFrame()
    if driver_laps.empty:
        st.warning("No lap timing rows for this driver. The position file may still be explored as a full-session path.")
        st.stop()
    lap_numbers = driver_laps["lap_number"].dropna().astype(int).drop_duplicates().tolist()
    selected_lap = st.selectbox("Select lap", lap_numbers)
    lap_row = get_lap_row(laps, chosen_number, selected_lap)
    if lap_row is None or pd.isna(lap_row.get("date_start")) or pd.isna(lap_row.get("lap_duration")):
        st.warning("Lap timestamp unavailable.")
        st.stop()

    start = lap_row["date_start"]
    duration = float(lap_row["lap_duration"])
    begin = start - pd.Timedelta(seconds=.8)
    end = start + pd.Timedelta(seconds=duration + .8)
    path = location[location["driver_number"] == chosen_number].copy()
    path = path[(path["date"] >= begin) & (path["date"] <= end)].dropna(subset=["x", "y"]).sort_values("date")
    if path.empty:
        st.warning("No position points found during this lap. Try another lap.")
        st.stop()

    car = telemetry[telemetry["driver_number"] == chosen_number].copy().dropna(subset=["date"]).sort_values("date")
    if not car.empty and "speed" in car.columns:
        path = pd.merge_asof(path.sort_values("date"), car[["date", "speed"]].dropna(subset=["date"]).sort_values("date"), on="date", direction="nearest", tolerance=pd.Timedelta(milliseconds=700))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=path["x"], y=path["y"], mode="lines", name="Car path", line=dict(color="#65758b", width=2.5)))
    if "speed" in path.columns and path["speed"].notna().any():
        fig.add_trace(go.Scatter(
            x=path["x"], y=path["y"], mode="markers", name="Speed",
            marker=dict(size=6, color=path["speed"], colorscale="Turbo", colorbar=dict(title="km/h"), showscale=True),
            text=[f"Speed: {v:.0f} km/h" if pd.notna(v) else "Speed unavailable" for v in path["speed"]],
            hovertemplate="X: %{x}<br>Y: %{y}<br>%{text}<extra></extra>",
        ))
    fig.add_trace(go.Scatter(x=[path.iloc[0]["x"]], y=[path.iloc[0]["y"]], mode="markers+text", name="START", text=["START"], textposition="top center", marker=dict(size=12, color="#20d9a0", symbol="circle")))
    fig.update_layout(title=f"{code_by_number.get(chosen_number, chosen_number)} — lap {selected_lap}", xaxis_title="X coordinate (OpenF1)", yaxis_title="Y coordinate (OpenF1)", yaxis=dict(scaleanchor="x", scaleratio=1), **PLOT_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("OpenF1 x/y coordinates are approximate Cartesian telemetry. The view is useful for visualizing a car path, but it is not an official or surveyed circuit map.")

# ------------------------------------------------------------
# LAP DATA
# ------------------------------------------------------------
elif page == "Lap Data":
    section_heading("TIMING & SECTORS", "Lap data explorer")
    if laps.empty:
        st.warning("The file data/all_drivers_laps.csv is missing or empty.")
        st.stop()
    best = best_laps_table(laps, drivers)
    if not best.empty:
        view = best.copy()
        view["Lap time"] = view["lap_duration"].apply(format_lap_time)
        desired = [c for c in ["name_acronym", "full_name", "team_name", "lap_number", "Lap time", "duration_sector_1", "duration_sector_2", "duration_sector_3", "i1_speed", "i2_speed", "st_speed"] if c in view.columns]
        view = view[desired].rename(columns={
            "name_acronym": "Code", "full_name": "Driver", "team_name": "Team", "lap_number": "Lap",
            "duration_sector_1": "Sector 1 (s)", "duration_sector_2": "Sector 2 (s)", "duration_sector_3": "Sector 3 (s)",
            "i1_speed": "I1 speed (km/h)", "i2_speed": "I2 speed (km/h)", "st_speed": "Speed trap (km/h)",
        })
        st.dataframe(view, use_container_width=True, hide_index=True)
    st.markdown("**All recorded laps**")
    st.dataframe(laps, use_container_width=True, hide_index=True)

st.divider()
st.markdown(
    '<div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;color:#78899f;font-size:.70rem;letter-spacing:.08em"><span>F1 TELEMETRY ANALYZER • VISUAL EDITION 6.1</span><span>INDEPENDENT EDUCATIONAL PROJECT • DATA: OPENF1</span></div>',
    unsafe_allow_html=True,
)
