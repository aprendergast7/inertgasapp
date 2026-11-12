import streamlit as st
import datetime
import json

st.set_page_config(page_title="Inert Gas App", layout="centered")

STEPS = [
    "Space", "Normal ops", "Container",
    "SPOF", "Review", "Screening", "Controls"
]

UNIT_LABEL = {
    "metric": {"len": "m", "vol": "m3", "air": "m3/hr", "gas": "LPM"},
    "imperial": {"len": "ft", "vol": "ft3", "air": "cfm", "gas": "CFM"}
}

GAS_TYPES = [
    "Nitrogen (N2)", "Argon (Ar)",
    "Helium (He)", "Carbon Dioxide (CO2)"
]

CRYOGEN_TYPES = [
    "Liquid Nitrogen (LIN)",
    "Liquid Argon (LAR)",
    "Liquid Helium (LHe)"
]

SCENARIOS = [
    {
        "id": "cat_a_confined",
        "title": "Confined Space / Entering Tanks or Vaults",
        "category": "A",
        "detail": "Confined space with O2 deficiency potential.",
        "oda": False,
        "odaNote": "No (Confined Space Standard governs)",
        "controlsTitle": "Category A - Confined Space Controls",
        "controls": [
            "Attendants required prior to and during entry.",
            "Atmospheric testing before entry (O2 > 19.5%).",
            "Formal Confined Space Entry Permits required."
        ]
    },
    {
        "id": "cat_a_enclosed",
        "title": "Enclosed Space (Not confined space)",
        "category": "A",
        "detail": "E.g. WIPP storage, chambers, large N2 cabinets.",
        "oda": False,
        "odaNote": "No (Forced air & prior monitoring governs)",
        "controlsTitle": "Category A - Enclosed Space Controls",
        "controls": [
            "Lockout/Tagout (LOTO) inert gas before entry.",
            "Forced air mechanical ventilation required.",
            "Post hazard warning signs at entry points.",
            "Prior atmospheric testing before entry."
        ]
    },
    {
        "id": "cat_b1",
        "title": "Normal Operations Potential Deficit",
        "category": "B-1",
        "detail": "Normal release with O2 drop < 19.5% (Dewars/purge).",
        "oda": True,
        "odaNote": "Yes (Quantitative ODA Mandatory)",
        "controlsTitle": "Category B-1 - Normal Release Controls",
        "controls": [
            "Complete formal Quantitative ODA.",
            "Mechanical ventilation to keep O2 > 19.5%.",
            "Engineered flow restrictions or O2 monitors."
        ]
    },
    {
        "id": "cat_b2",
        "title": "Accidental Release Deficit (SPOF)",
        "category": "B-2",
        "detail": "Accidental release O2 < 16% & low warning.",
        "oda": True,
        "odaNote": "Yes (Quantitative ODA Mandatory)",
        "controlsTitle": "Category B-2 - Accidental Release Controls",
        "controls": [
            "Complete Quantitative ODA for SPOF.",
            "Secondary containment or continuous O2 monitor.",
            "Ensure acces
