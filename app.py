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
    "imperial": {"len": "ft", "vol": "ft³", "air": "cfm", "gas": "CFM"}
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
            "Attendants required prior to and during entry
