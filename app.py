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
            "Prior atmospheric testing required before entry."
        ]
    },
    {
        "id": "cat_b1",
        "title": "Normal Operations Potential Deficit",
        "category": "B-1",
        "detail": "Normal release potential with O2 drop < 19.5% (e.g., Dewars, line purging).",
        "oda": True,
        "odaNote": "Yes (Quantitative ODA Mandatory)",
        "controlsTitle": "Category B-1 · Normal Release Controls",
        "controls": [
            "Complete a formal Quantitative Oxygen Deficiency Assessment (ODA).",
            "Provide mechanical ventilation to maintain O2 > 19.5%.",
            "Install engineered flow restrictions or continuous O2 monitors."
        ]
    },
    {
        "id": "cat_b2",
        "title": "Accidental Release Deficit (SPOF)",
        "category": "B-2",
        "detail": "Accidental release potential with O2 drop < 16% & low warning properties (noise > 85 dBA or inaudible leak).",
        "oda": True,
        "odaNote": "Yes (Quantitative ODA Mandatory)",
        "controlsTitle": "Category B-2 · Accidental Release Controls",
        "controls": [
            "Complete Quantitative ODA for Single Point of Failure (SPOF).",
            "Provide secondary containment/controls or continuous O2 monitoring where O2 can fall <= 16%.",
            "Ensure accessible emergency shut-off valves."
        ]
    },
    {
        "id": "cat_c_clean",
        "title": "Low Potential (Normal Release / Cleanrooms)",
        "category": "C",
        "detail": "Continuous purge with high dilution ventilation (ratio > 23:1 or > 15:1 in fabs) and no gas pockets.",
        "oda": False,
        "odaNote": "No (Provided automatic evacuation on HVAC fail exists)",
        "controlsTitle": "Category C · Low Potential (Cleanrooms)",
        "controls": [
            "Maintain required dilution ventilation ratios.",
            "Ensure automatic evacuation systems are tied to HVAC system failures.",
            "Apply proper hazard awareness labeling."
        ]
    },
    {
        "id": "cat_c_tubing",
        "title": "Low Potential (Accidental Release / Tubing & Cylinders)",
        "category": "C",
        "detail": "Lines in well-ventilated spaces, outdoor venting, or closed cylinder valves where accidental release keeps O2 >= 16%.",
        "oda": False,
        "odaNote": "No",
        "controlsTitle": "Category C · Low Potential (Tubing/Cylinders)",
        "controls": [
            "Verify gas delivery compliance check.",
            "Restrict tubing failures to max inaudible leaks of 0.235 scfm (controlled by general ventilation).",
            "Perform periodic exhaust inspection."
        ]
    },
    {
        "id": "cat_d",
        "title": "Outdoor Areas",
        "category": "D",
        "detail": "Large-volume bulk gas or cryogen use/storage fully open to outside air.",
        "oda": False,
        "odaNote": "No",
        "controlsTitle": "Category D · Outdoor Controls",
        "controls": [
            "Enforce access restrictions (fencing/gates).",
            "Ensure proper bulk tank labeling and warning signs.",
            "Provide training on written transfer procedures."
        ]
    }
]

# --- Helper Functions ---
def get_scenario(sc_id):
    return next((s for s in SCENARIOS if s["id"] == sc_id), None)

def calc_room_volume(a):
    try:
        if a["volumeDirect"]:
            return round(float(a["volume"]), 2) if a["volume"] else None
        l, w, h = float(a["length"]), float(a["width"]), float(a["height"])
        if l > 0 and w > 0 and h > 0:
            return round(l * w * h, 2)
    except ValueError:
        pass
    return None

def suggest_scenario(a):
    """Heuristic engine mimicking suggestScenario(a)"""
    if a["normal"]["enabled"] or a["container"]["enabled"]:
        if a["hvac"] and a.get("roomFlow") and float(a.get("roomFlow") or 0) > 1000:
            return "cat_c_clean"
        return "cat_b1"
    if a["spof"]["enabled"]:
        if not a["spof"]["quiet"] or not a["spof"]["ventilation"] or a["spof"]["threaded"]:
            return "cat_b2"
        return "cat_c_tubing"
    if not a["hvac"] and float(a.get("openness") or 0) >= 80:
        return "cat_d"
    return "cat_c_tubing"

def choice_input(label, options, current_val, key_prefix):
    """Mimics the custom <Choice /> pill component with 'Other' text input"""
    is_custom = current_val not in options and current_val != ""
    radio_opts = options + ["Other"]
    default_idx = len(options) if is_custom else (options.index(current_val) if current_val in options else 0)
    
    selected = st.radio(label, radio_opts, index=default_idx, horizontal=True, key=f"{key_prefix}_radio")
    if selected == "Other":
        return st.text_input("Specify custom type:", value=current_val if is_custom else "", placeholder="Type gas name...", key=f"{key_prefix}_custom")
    return selected

# ==============================================================================
# TRANSLATED SUMMARY.TSX LOGIC
# ==============================================================================
def format_date(iso_str):
    try:
        dt = datetime.date.fromisoformat(iso_str)
        return dt.strftime("%B %d, %Y")
    except ValueError:
        return iso_str

def summary_rows(a):
    u = UNIT_LABEL[a["units"]]
    v = calc_room_volume(a)
    
    def f(x, unit=""):
        return "—" if x is None else f"{round(x, 2)}{unit}"
        
    def yn(b):
        return "Yes" if b else "No"
        
    def val(s, unit):
        return f"{s} {unit}" if s else "—"

    # Compile the precise sections and keys returned by summaryRows()
    sections = [
        ("Date & location", [
            ("Date", format_date(a["date"])),
            ("Assessor", a["assessor"] if a["assessor"] else "—"),
            ("Building / floor", a["building"] if a["building"] else "—"),
            ("Room / area", a["room"] if a["room"] else "—")
        ]),
        ("Volume & layout", [
            ("Units", "Metric" if a["units"] == "metric" else "Imperial"),
            ("Dimensions", "Entered directly" if a["volumeDirect"] else f"{a['length'] or '?'} × {a['width'] or '?'} × {a['height'] or '?'} {u['len']}"),
            ("Room volume", f(v, f" {u['vol']}")),
            ("Barriers", yn(a["barriers"])),
            ("Openness", f"{a['openness']}%" if a["openness"] else "—")
        ]),
        ("HVAC", [
            ("HVAC", "Yes"),
            ("Sector AHU flow", val(a["ahuFlow"], u["air"])),
            ("Outside air", f"{a['outsideAirPct']}%" if a["outsideAirPct"] else "—"),
            ("Room HVAC flow", val(a["roomFlow"], u["air"])),
            ("K-factor", str(a["kFactor"]))
        ] if a["hvac"] else [("HVAC", "No")]),
        ("Releases", [
            ("Normal operations", f"Yes · {a['normal']['gas'] or '—'} · {val(a['normal']['flow'], u['gas'])}" if a["normal"]["enabled"] else "No"),
            ("Finite container", f"Yes · {a['container']['cryogen'] or '—'} · {val(a['container']['litres'], 'L')}" if a["container"]["enabled"] else "No"),
            ("Single point of failure", f"Yes · {a['spof']['gas'] or '—'} · {val(a['spof']['flow'], u['gas'])}" if a["spof"]["enabled"] else "No"),
        ])
    ]

    # Add conditional SPOF items exactly like ...(a.spof.enabled ? [...] : [])
    if a["spof"]["enabled"]:
        sections[3][1].extend([
            ("Threaded fittings", yn(a["spof"]["threaded"])),
            ("Ventilation in space", yn(a["spof"]["ventilation"])),
            ("Sound < 85 dBA", yn(a["spof"]["quiet"]))
        ])
        
    return sections

# --- Initialize Session State ---
if "step" not in st.session_state:
    st.session_state.step = 0

if "a" not in st.session_state:
    st.session_state.a = {
        "id": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        "assessor": "",
        "date": datetime.date.today().isoformat(),
        "building": "",
        "room": "",
        "units": "metric",
        "volumeDirect": False,
        "volume": "",
        "length": "",
        "width": "",
        "height": "",
        "barriers": False,
        "openness": "100",
        "hvac": True,
        "ahuFlow": "",
        "outsideAirPct": "",
        "roomFlow": "",
        "kFactor": 1,
        "normal": {"enabled": False, "gas": GAS_TYPES[0], "flow": ""},
        "container": {"enabled": False, "cryogen": CRYOGEN_TYPES[0], "litres": ""},
        "spof": {"enabled": False, "gas": GAS_TYPES[0], "flow": "", "threaded": False, "ventilation": True, "quiet": True},
        "photos": [],
        "scenario": "",
        "notes": ""
    }

a = st.session_state.a
step = st.session_state.step
u = UNIT_LABEL[a["units"]]
vol = calc_room_volume(a)

# --- Top Progress Bar & Navigation ---
st.markdown("### 💨 Inert Gas Assessment")
cols = st.columns(len(STEPS))
for i, s_name in enumerate(STEPS):
    with cols[i]:
        if i < step:
            if st.button(f"✓ {s_name}", key=f"nav_{i}", use_container_width=True):
                st.session_state.step = i
                st.rerun()
        elif i == step:
            st.markdown(f"<div style='text-align:center; background:#1e40af; color:white; padding:6px; border-radius:6px; font-size:12px; font-weight:bold;'>{s_name}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:center; background:#e2e8f0; color:#64748b; padding:6px; border-radius:6px; font-size:12px;'>{s_name}</div>", unsafe_allow_html=True)

st.caption(f"**STEP {step + 1} OF {len(STEPS)} · {STEPS[step].upper()}**")
st.markdown("---")

# ==============================================================================
# STEP 0: SPACE DETAILS
# ==============================================================================
if step == 0:
    st.subheader("1 · Space details")
    a["assessor"] = st.text_input("ASSESSOR", value=a["assessor"], placeholder="Your name")
    
    c1, c2 = st.columns(2)
    with c1:
        d_val = datetime.date.fromisoformat(a["date"]) if a["date"] else datetime.date.today()
        a["date"] = st.date_input("DATE", value=d_val).isoformat()
    with c2:
        a["building"] = st.text_input("BUILDING / FLOOR", value=a["building"], placeholder="e.g. B2, Level 1")
        
    a["room"] = st.text_input("ROOM / AREA", value=a["room"], placeholder="e.g. Cryo lab 104")
    
    unit_choice = st.radio(
        "UNITS",
        options=["metric", "imperial"],
        format_func=lambda x: "Metric (m, LPM)" if x == "metric" else "Imperial (ft, CFM)",
        index=0 if a["units"] == "metric" else 1,
        horizontal=True
    )
    if unit_choice != a["units"]:
        a["units"] = unit_choice
        st.rerun()

    st.markdown("#### Dimensions & volume")
    a["volumeDirect"] = st.toggle("Enter total room volume directly", value=a["volumeDirect"])
    if a["volumeDirect"]:
        a["volume"] = st.text_input(f"TOTAL ROOM VOLUME ({u['vol']})", value=a["volume"])
    else:
        vc1, vc2, vc3 = st.columns(3)
        with vc1:
            a["length"] = st.text_input(f"LENGTH ({u['len']})", value=a["length"])
        with vc2:
            a["width"] = st.text_input(f"WIDTH ({u['len']})", value=a["width"])
        with vc3:
            a["height"] = st.text_input(f"HEIGHT ({u['len']})", value=a["height"])
            
    vol = calc_room_volume(a)
    st.info(f"Room volume: **{f'{vol} {u[\"vol\"]}' if vol is not None else '—'}**")

    st.markdown("#### Physical layout")
    a["barriers"] = st.toggle("Barriers within the room (curtains, shielding)", value=a["barriers"])
    a["openness"] = st.text_input("ROOM OPENNESS (%)", value=a["openness"])

    st.markdown("#### HVAC & ventilation")
    a["hvac"] = st.toggle("HVAC in operation", value=a["hvac"])
    if a["hvac"]:
        hc1, hc2 = st.columns(2)
        with hc1:
            a["ahuFlow"] = st.text_input(f"SECTOR AHU FLOW RATE ({u['air']})", value=a["ahuFlow"])
            a["roomFlow"] = st.text_input(f"ROOM HVAC FLOW RATE ({u['air']})", value=a["roomFlow"])
        with hc2:
            a["outsideAirPct"] = st.text_input("OUTSIDE AIR (%)", value=a["outsideAirPct"])
            a["kFactor"] = st.selectbox("K-FACTOR (MIXING EFFICIENCY, 1 = BEST)", options=[1, 2, 3, 4, 5, 6, 7, 8], index=a["kFactor"] - 1)

# ==============================================================================
# STEP 1: NORMAL OPERATIONS RELEASE
# ==============================================================================
elif step == 1:
    st.subheader("2 · Normal operations release")
    st.caption("Planned, continuous or cyclic releases during standard processes.")
    
    a["normal"]["enabled"] = st.toggle("Normal operations release?", value=a["normal"]["enabled"])
    if a["normal"]["enabled"]:
        a["normal"]["gas"] = choice_input("GAS TYPE", GAS_TYPES, a["normal"]["gas"], "norm_gas")
        a["normal"]["flow"] = st.text_input(f"MAX FLOW RATE ({u['gas']})", value=a["normal"]["flow"])

# ==============================================================================
# STEP 2: FINITE CONTAINER
# ==============================================================================
elif step == 2:
    st.subheader("3 · Finite single source container")
    st.caption("Dewars, cryogens, cylinders.")
    
    a["container"]["enabled"] = st.toggle("Finite single source container?", value=a["container"]["enabled"])
    if a["container"]["enabled"]:
        a["container"]["cryogen"] = choice_input("CRYOGEN TYPE", CRYOGEN_TYPES, a["container"]["cryogen"], "cont_cryo")
        a["container"]["litres"] = st.text_input("VOLUME (LITRES)", value=a["container"]["litres"])

# ==============================================================================
# STEP 3: SPOF
# ==============================================================================
elif step == 3:
    st.subheader("4 · Probable single point of failure")
    st.caption("Accidental release from pressurised lines or hardware failure.")
    
    a["spof"]["enabled"] = st.toggle("Probable single point of failure?", value=a["spof"]["enabled"])
    if a["spof"]["enabled"]:
        a["spof"]["gas"] = choice_input("GAS TYPE", GAS_TYPES, a["spof"]["gas"], "spof_gas")
        a["spof"]["flow"] = st.text_input(f"FLOW RATE ({u['gas']})", value=a["spof"]["flow"])
        a["spof"]["threaded"] = st.toggle("All threaded fittings?", value=a["spof"]["threaded"])
        a["spof"]["ventilation"] = st.toggle("Ventilation in space?", value=a["spof"]["ventilation"])
        a["spof"]["quiet"] = st.toggle("Sound level < 85 dBA?", value=a["spof"]["quiet"])

# ==============================================================================
# STEP 4: DATA SUMMARY REVIEW (INTEGRATED WITH SUMMARY.TSX)
# ==============================================================================
elif step == 4:
    st.subheader("DATA SUMMARY REVIEW")
    
    # Renders each section dynamically from summary_rows() using dl grid design
    for section_title, rows in summary_rows(a):
        with st.container(border=True):
            st.markdown(f"##### {section_title}")
            for k, v in rows:
                col_k, col_v = st.columns([1, 2])
                with col_k:
                    st.markdown(f"<span style='color: #64748b; font-size:15px;'>{k}</span>", unsafe_allow_html=True)
                with col_v:
                    st.markdown(f"<span style='font-weight: 500; font-size:15px;'>{v}</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📷 Photos")
    st.caption("Optional – upload photos of the space")
    uploaded_files = st.file_uploader("Add photo", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
    if uploaded_files:
        for uf in uploaded_files:
            if not any(p["name"] == uf.name for p in a["photos"]):
                a["photos"].append({"name": uf.name, "bytes": uf.getvalue(), "caption": ""})

    if a["photos"]:
        p_cols = st.columns(2)
        for idx, p in enumerate(a["photos"]):
            with p_cols[idx % 2]:
                st.image(p["bytes"], use_container_width=True)
                p["caption"] = st.text_input("Caption", value=p["caption"], key=f"cap_{idx}", placeholder="Caption")
                if st.button("🗑️ Remove photo", key=f"del_{idx}"):
                    a["photos"].pop(idx)
                    st.rerun()

# ==============================================================================
# STEP 5: QUALITATIVE SCREENING
# ==============================================================================
elif step == 5:
    st.subheader("Qualitative screening")
    st.caption("Choose the condition that best describes this space.")
    
    suggested_id = suggest_scenario(a)
    suggested_sc = get_scenario(suggested_id)
    if suggested_sc:
        st.info(f"💡 Based on your inputs, the indicative estimate points to **{suggested_sc['title']}**. Confirm or choose another.")

    for s in SCENARIOS:
        is_selected = (a["scenario"] == s["id"])
        with st.container(border=True):
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"**{s['title']}** {'✅' if is_selected else ''}")
                st.caption(s["detail"])
                st.markdown(f"<span style='font-size:12px; font-weight:600;'>ODA required: {s['odaNote']}</span>", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"<div style='text-align:right;'><span style='background:#e2e8f0; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:bold;'>Cat {s['category']}</span></div>", unsafe_allow_html=True)
                if st.button("Select" if not is_selected else "Selected", key=f"sel_{s['id']}", type="primary" if is_selected else "secondary", use_container_width=True):
                    a["scenario"] = s["id"]
                    st.rerun()

# ==============================================================================
# STEP 6: CONTROLS & NOTES
# ==============================================================================
elif step == 6:
    sc = get_scenario(a["scenario"])
    if sc:
        st.subheader(sc["controlsTitle"])
        if sc["oda"]:
            st.error(f"**Quantitative ODA required:** {sc['odaNote']}")
        else:
            st.success(f"**Quantitative ODA required:** {sc['odaNote']}")

        st.markdown("#### Mandatory Controls:")
        for c in sc["controls"]:
            st.markdown(f"✅ {c}")

    st.markdown("#### Notes")
    a["notes"] = st.text_area("Optional comments or actions required…", value=a["notes"], height=100)

# ==============================================================================
# BOTTOM NAVIGATION BAR
# ==============================================================================
st.markdown("---")
nav_col1, nav_col2 = st.columns(2)

if step == 4:
    with nav_col1:
        if st.button("Edit details", use_container_width=True):
            st.session_state.step = 0
            st.rerun()
    with nav_col2:
        if st.button("Proceed →", type="primary", use_container_width=True):
            st.session_state.step = 5
            st.rerun()
else:
    with nav_col1:
        if step > 0:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = step - 1
                st.rerun()
    with nav_col2:
        if step < 6:
            btn_label = "Submit evaluation →" if step == 5 else "Next →"
            if st.button(btn_label, type="primary", use_container_width=True):
                # Validation matching next() in AssessmentForm.tsx
                if step == 0:
                    if not a["assessor"].strip():
                        st.error("Add the assessor's name")
                        st.stop()
                    if not a["building"].strip() and not a["room"].strip():
                        st.error("Add the building or room")
                        st.stop()
                if step == 5 and not a["scenario"]:
                    st.error("Choose the condition that applies")
                    st.stop()
                st.session_state.step = step + 1
                st.rerun()
        else:
            if st.button("💾 Save & register space", type="primary", use_container_width=True):
                # Save locally as JSON (excluding raw image bytes for clean JSON serialization)
                save_payload = {k: v for k, v in a.items() if k != "photos"}
                save_payload["photo_captions"] = [p["caption"] for p in a["photos"]]
                filename = f"assessment_{a['id']}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(save_payload, f, indent=2)
                st.toast(f"Assessment saved locally as {filename}!", icon="✅")
                st.success(f"✅ Assessment saved on this device as `{filename}`!")
                st.download_button(
                    "⬇️ Download Assessment JSON",
                    data=json.dumps(save_payload, indent=2),
                    file_name=filename,
                    mime="application/json",
                    use_container_width=True
                )
