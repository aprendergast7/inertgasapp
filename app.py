import streamlit as st
import datetime
import json
import os

# --- Page Config ---
st.set_page_config(
    page_title="Inert Gas Assessment",
    page_icon="💨",
    layout="centered"
)

# --- Constants & Reference Data ---
STEPS = ["Space", "Normal ops", "Container", "SPOF", "Review", "Screening", "Controls"]

UNIT_LABEL = {
    "metric": {"len": "m", "vol": "m³", "air": "m³/hr", "gas": "LPM"},
    "imperial": {"len": "ft", "vol": "ft³", "air": "cfm", "gas": "CFM"},
}

GAS_TYPES = ["Nitrogen (N2)", "Argon (Ar)", "Helium (He)", "Carbon Dioxide (CO2)"]
CRYOGEN_TYPES = ["Liquid Nitrogen (LIN)", "Liquid Argon (LAR)", "Liquid Helium (LHe)"]

SCENARIOS = [
    {
        "id": "cat_a_confined",
        "title": "Confined Space / Entering Tanks or Vaults",
        "category": "A",
        "detail": "Meets confined space definition with O2 deficiency potential.",
        "oda": False,
        "odaNote": "No (Confined Space Standard governs)",
        "controlsTitle": "Category A · Confined Space Controls",
        "controls": [
            "Attendants required prior to and during entry.",
            "Atmospheric testing prior to entry (verify O2 > 19.5%).",
            "Formal Confined Space Entry Permits required."
        ]
    },
    {
        "id": "cat_a_enclosed",
        "title": "Enclosed Space (Entry possible, not confined space)",
        "category": "A",
        "detail": "E.g., WIPP storage, walk-in chambers, or large N2 cabinets.",
        "oda": False,
        "odaNote": "No (Forced air & prior monitoring governs)",
        "controlsTitle": "Category A · Enclosed Space Controls",
        "controls": [
            "Lockout / Tagout (LOTO) inert gas supplies prior to entry.",
            "Forced air mechanical ventilation required.",
            "Post clear hazard warning signs at entry points.",
    
