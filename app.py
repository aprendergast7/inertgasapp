import streamlit as st
import datetime

# --- Page Config ---
st.set_page_config(
    page_title="Inert Gas Hazard & ODA Screening",
    page_icon="💨",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Title & Header ---
st.title("💨 Inert Gas Hazard & ODA Screening App")
st.markdown("""
This EHS application helps evaluate workspaces using inert gases, screens for qualitative risk categories (A, B, C, or D), 
and outlines the mandatory corporate safety controls.
---
""")

# --- Sidebar Configuration ---
st.sidebar.header("🛠️ Application Settings")

unit_system = st.sidebar.radio(
    "Measurement Unit System",
    ["Metric", "Imperial"],
    help="Select units for room dimensions and flow rates. Note: Finite source container volumes are always recorded in Litres."
)

# Define Unit Label Dict
if unit_system == "Metric":
    units = {"length": "meters (m)", "volume": "m³", "hvacFlow": "m³/hr", "gasFlow": "LPM"}
else:
    units = {"length": "feet (ft)", "volume": "ft³", "hvacFlow": "cfm", "gasFlow": "CFM"}

# --- App State Navigation ---
if "step" not in st.session_state:
    st.session_state.step = 1

# Helper to progress steps
def set_step(step_num):
    st.session_state.step = step_num

# ==============================================================================
# STEP 1: DATA ENTRY
# ==============================================================================
if st.session_state.step == 1:
    st.subheader("📋 Step 1: Space & Release Parameters")
    
    with st.form("data_entry_form"):
        # Section 1: Space Details
        st.markdown("### Section 1 – Space Details")
        col1, col2, col3 = st.columns(3)
        with col1:
            date_val = st.date_input("Assessment Date", datetime.date.today())
        with col2:
            building_floor = st.text_input("Building / Floor", placeholder="e.g., Fab 24 / Floor 2")
        with col3:
            room_area = st.text_input("Room / Area", placeholder="e.g., Sub-fab Gas Pad B")

        # Volume Mode Selection
        vol_mode = st.radio(
            "Volume Calculation Method",
            ["Enter Room Dimensions (Length × Width × Height)", "Enter Total Room Volume Directly"],
            horizontal=True
        )

        room_volume = 0.0
        if "Dimensions" in vol_mode:
            v_col1, v_col2, v_col3 = st.columns(3)
            with v_col1:
                length = st.number_input(f"Length ({units['length']})", min_value=0.0, step=0.1, format="%.2f")
            with v_col2:
                width = st.number_input(f"Width ({units['length']})", min_value=0.0, step=0.1, format="%.2f")
            with v_col3:
                height = st.number_input(f"Height ({units['length']})", min_value=0.0, step=0.1, format="%.2f")
            room_volume = round(length * width * height, 2)
            st.info(f"📐 **Calculated Volume:** {room_volume} {units['volume']}")
        else:
            room_volume = st.number_input(f"Total Room Volume ({units['volume']})", min_value=0.0, step=1.0)

        # Layout Modifiers
        l_col1, l_col2, l_col3 = st.columns(3)
        with l_col1:
            has_barriers = st.selectbox("Barriers Present in Room?", ["No", "Yes"])
        with l_col2:
            room_openness = st.slider("Room Openness (%)", min_value=0, max_value=100, value=100)
        with l_col3:
            has_hvac = st.selectbox("Mechanical HVAC Active?", ["Yes", "No"])

        # Conditional HVAC Input
        sector_ahu_flow = 0.0
        outside_air_pct = 0.0
        room_hvac_flow = 0.0
        k_factor = 1
        
        if has_hvac == "Yes":
            st.markdown("##### HVAC Ventilation Configuration")
            h_col1, h_col2, h_col3, h_col4 = st.columns(4)
            with h_col1:
                sector_ahu_flow = st.number_input(f"Sector AHU Flow ({units['hvacFlow']})", min_value=0.0, step=10.0)
            with h_col2:
                outside_air_pct = st.number_input("Outside Air (%)", min_value=0.0, max_value=100.0, step=1.0)
            with h_col3:
                room_hvac_flow = st.number_input(f"Room HVAC Flow ({units['hvacFlow']})", min_value=0.0, step=10.0)
            with h_col4:
                k_factor = st.selectbox("Mixing K-Factor", [1, 2, 3, 4, 5, 6, 7, 8], index=0)

        # Section 2: Normal Operations Release
        st.markdown("---")
        st.markdown("### Section 2 – Normal Operations Release")
        has_normal_release = st.selectbox("Is there a normal operations release?", ["No", "Yes"])
        normal_gas_type = ""
        normal_max_flow = 0.0
        if has_normal_release == "Yes":
            n_col1, n_col2 = st.columns(2)
            with n_col1:
                normal_gas_type = st.selectbox("Gas Type (Normal)", ["Nitrogen (N2)", "Argon (Ar)", "Helium (He)", "Carbon Dioxide (CO2)", "Other"])
            with n_col2:
                normal_max_flow = st.number_input(f"Max Flow Rate ({units['gasFlow']})", min_value=0.0, step=1.0)

        # Section 3: Finite Single Source Container
        st.markdown("---")
        st.markdown("### Section 3 – Finite Single Source Container")
        has_finite_source = st.selectbox("Is there a finite single source container (e.g., Dewar, Cylinder)?", ["No", "Yes"])
        cryogen_type = ""
        finite_volume_litres = 0.0
        if has_finite_source == "Yes":
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                cryogen_type = st.selectbox("Cryogen / Gas Source Type", ["Liquid Nitrogen (LIN)", "Liquid Argon (LAR)", "Liquid Helium (LHe)", "Compressed Gas Cylinder"])
            with f_col2:
                finite_volume_litres = st.number_input("Container Volume (Mandated in Litres)", min_value=0.0, step=1.0)

        # Section 4: Probable SPOF Release
        st.markdown("---")
        st.markdown("### Section 4 – Probable Single Point of Failure (SPOF) Release")
        has_spof_release = st.selectbox("Is there a probable SPOF release hazard?", ["No", "Yes"])
        spof_gas_type = ""
        spof_flow_rate = 0.0
        all_threaded_fittings = "No"
        ventilation_in_space = "Yes"
        sound_under_85 = "Yes"
        
        if has_spof_release == "Yes":
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                spof_gas_type = st.selectbox("SPOF Gas Type", ["Nitrogen (N2)", "Argon (Ar)", "Helium (He)", "Carbon Dioxide (CO2)"])
            with s_col2:
                spof_flow_rate = st.number_input(f"SPOF Flow Rate ({units['gasFlow']})", min_value=0.0, step=1.0)
            
            s_col3, s_col4, s_col5 = st.columns(3)
            with s_col3:
                all_threaded_fittings = st.selectbox("All Threaded Fittings?", ["No", "Yes"])
            with s_col4:
                ventilation_in_space = st.selectbox("Local Ventilation in Space?", ["Yes", "No"])
            with s_col5:
                sound_under_85 = st.selectbox("Background Sound Level < 85 dBA?", ["Yes", "No"])

        # Submit to session state
        submit_btn = st.form_submit_button("Review Space & Release Inputs →")
        if submit_btn:
            st.session_state.form_data = {
                "date": date_val, "building_floor": building_floor, "room_area": room_area,
                "room_volume": room_volume, "has_barriers": has_barriers, "room_openness": room_openness,
                "has_hvac": has_hvac, "sector_ahu_flow": sector_ahu_flow, "outside_air_pct": outside_air_pct,
                "room_hvac_flow": room_hvac_flow, "k_factor": k_factor, "has_normal_release": has_normal_release,
                "normal_gas_type": normal_gas_type, "normal_max_flow": normal_max_flow,
                "has_finite_source": has_finite_source, "cryogen_type": cryogen_type,
                "finite_volume_litres": finite_volume_litres, "has_spof_release": has_spof_release,
                "spof_gas_type": spof_gas_type, "spof_flow_rate": spof_flow_rate,
                "all_threaded_fittings": all_threaded_fittings, "ventilation_in_space": ventilation_in_space,
                "sound_under_85": sound_under_85
            }
            set_step(2)
            st.rerun()

# ==============================================================================
# STEP 2: VERIFICATION & REVIEW
# ==============================================================================
elif st.session_state.step == 2:
    st.subheader("🔍 Step 2: Verify Input Space Details")
    data = st.session_state.form_data

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🏢 Space & Mechanical Parameters")
        st.write(f"**Date of Evaluation:** {data['date']}")
        st.write(f"**Location:** {data['building_floor']} / {data['room_area']}")
        st.write(f"**Calculated Room Volume:** {data['room_volume']} {units['volume']}")
        st.write(f"**Barriers Present:** {data['has_barriers']}")
        st.write(f"**Room Openness:** {data['room_openness']}%")
        st.write(f"**Mechanical Ventilation (HVAC):** {data['has_hvac']}")
        if data['has_hvac'] == "Yes":
            st.write(f"- *Sector AHU Flow:* {data['sector_ahu_flow']} {units['hvacFlow']} ({data['outside_air_pct']}% Outside Air)")
            st.write(f"- *Dedicated Room Flow:* {data['room_hvac_flow']} {units['hvacFlow']}")
            st.write(f"- *Mixing Efficiency K-Factor:* {data['k_factor']}")

    with col2:
        st.markdown("#### ⛽ Gas & Cryogen Releases")
        st.write(f"**Continuous/Normal Release:** {data['has_normal_release']}")
        if data['has_normal_release'] == "Yes":
            st.write(f"- *Gas Type:* {data['normal_gas_type']} | *Max Flow:* {data['normal_max_flow']} {units['gasFlow']}")
        
        st.write(f"**Finite Source Cryogens:** {data['has_finite_source']}")
        if data['has_finite_source'] == "Yes":
            st.write(f"- *Source:* {data['cryogen_type']} | *Volume:* {data['finite_volume_litres']} L")
            
        st.write(f"**SPOF Fail-Safe Release:** {data['has_spof_release']}")
        if data['has_spof_release'] == "Yes":
            st.write(f"- *Gas:* {data['spof_gas_type']} | *SPOF Flow Rate:* {data['spof_flow_rate']} {units['gasFlow']}")
            st.write(f"- *Fitting Type:* Threaded={data['all_threaded_fittings']} | Local Vent={data['ventilation_in_space']} | Quiet Area (&lt;85 dBA)={data['sound_under_85']}")

    st.markdown("---")
    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        if st.button("← Go Back & Edit", use_container_width=True):
            set_step(1)
            st.rerun()
    with btn_col2:
        if st.button("Verify & Continue to Risk Screening →", type="primary", use_container_width=True):
            set_step(3)
            st.rerun()

# ==============================================================================
# STEP 3: QUALITATIVE SCREENING
# ==============================================================================
elif st.session_state.step == 3:
    st.subheader("🛡️ Step 3: Qualitative Screening Assessment")
    st.markdown("Identify the operational scenario that matches your workspace deployment to evaluate risks:")

    scenarios = [
        {
            "id": "A-Confined",
            "scenario": "Confined Space Entry",
            "desc": "Entry into vessels, vaults, pits, or tanks with inert setups.",
            "category": "A (Confined Space)",
            "oda": "No",
            "details": "Governed directly by the Corporate Confined Space standard. Permit and Attendant required."
        },
        {
            "id": "A-Enclosed",
            "scenario": "Enclosed Space Entry (Non-Confined)",
            "desc": "Walk-in environmental testing cabinets or high-density N2 spaces.",
            "category": "A (Enclosed Space)",
            "oda": "No",
            "details": "Entry possible. Mandatory locked-out inert systems or atmospheric checks before entry."
        },
        {
            "id": "B-1",
            "scenario": "Normal Operation Deficit Risk",
            "desc": "Ongoing purges/dispensing (e.g., Dewars) that could reduce oxygen concentration below 19.5%.",
            "category": "B-1",
            "oda": "Yes",
            "details": "Continuous normal release hazard. Requires fixed ODMs or flow restriction orifices."
        },
        {
            "id": "B-2",
            "scenario": "SPOF Failure Deficit Risk",
            "desc": "High pressure pipe failure hazards where O2 can fall below 16% in high background noise (>85 dBA).",
            "category": "B-2",
            "oda": "Yes",
            "details": "Accidental release hazard. Requires worst-case ODA, coaxial piping, or continuous fixed monitors."
        },
        {
            "id": "C-Cleanroom",
            "scenario": "Cleanroom / Sub-Fab High Dilution",
            "desc": "Purging with high dilution rates (>23:1 general, or >15:1 in semiconductor fabs) with zero pocket potential.",
            "category": "C (Cleanrooms)",
            "oda": "No",
            "details": "Low risk. Provided auto-evacuation is dynamically interlocked with ventilation fans."
        },
        {
            "id": "C-Tubing",
            "scenario": "Well-Ventilated Low Flow (Pipes/Cylinders)",
            "desc": "Coaxial systems, outdoor venting lines, or small utility cylinders keeping O2 level >= 16%.",
            "category": "C (Tubing/Cylinders)",
            "oda": "No",
            "details": "Standard tubing leak limits inaudible release to 0.235 scfm, easily offset by normal general HVAC."
        },
        {
            "id": "D",
            "scenario": "Fully Outdoor Areas",
            "desc": "Bulk LIN storage farms or open-air cylinder yards with unlimited atmosphere dilution.",
            "category": "D",
            "oda": "No",
            "details": "Fenced tank facilities, localized warning signage, and written procedures for delivery transfers."
        }
    ]

    selected_id = st.radio(
        "Select the applicable hazard condition:",
        options=[s["id"] for s in scenarios],
        format_func=lambda x: f"{next(s['scenario'] for s in scenarios if s['id'] == x)} (Risk: {next(s['category'] for s in scenarios if s['id'] == x)})"
    )

    # Highlight selected scenario details
    selected_scenario = next(s for s in scenarios if s["id"] == selected_id)
    st.info(f"**Assigned Category:** Category {selected_scenario['category']} | **Quantitative ODA Required:** {selected_scenario['oda']}")
    st.markdown(f"💡 *{selected_scenario['details']}*")

    st.markdown("---")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("← Back to Verification", use_container_width=True):
            set_step(2)
            st.rerun()
    with btn_col2:
        if st.button("Generate EHS Report & Controls →", type="primary", use_container_width=True):
            st.session_state.selected_risk = selected_scenario
            set_step(4)
            st.rerun()

# ==============================================================================
# STEP 4: FINAL REPORT & CONTROLS MATRIX
# ==============================================================================
elif st.session_state.step == 4:
    st.subheader("📋 Step 4: Final Hazard Evaluation & Controls Report")
    
    data = st.session_state.form_data
    risk = st.session_state.selected_risk

    # Header Card
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:1.5rem; border-radius:10px; color:white; margin-bottom:1.5rem;">
        <h3 style="margin:0; color:white;">Inert Gas Hazard Evaluation Report</h3>
        <p style="margin:4px 0 0 0; font-size:14px; opacity:0.85;">
            Facility: {data['building_floor']} &mdash; Area: {data['room_area']} | Evaluated: {data['date']}
        </p>
    </div>
    """, unsafe_style_allowed=True)

    # Risk Metrics Columns
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Risk Classification", f"Category {risk['category']}")
    with c2:
        st.metric("Quantitative ODA Needed?", risk['oda'])

    # Controls Matrix Table
    st.markdown("### 🛠️ Mandatory EHS Controls Matrix")
    
    controls_map = {
        "A (Confined Space)": [
            "Manage workspace strictly under the Corporate Confined Space Standard.",
            "Mandate formal Entry Permits and trained Standby Attendants.",
            "Verify O2 > 19.5% with pre-entry atmospheric checks.",
            "Enforce continuous personal O2 detection monitors."
        ],
        "A (Enclosed Space)": [
            "Establish strict Lockout/Tagout (LOTO) protocols for inert lines prior to entry.",
            "Enforce mechanical purging/forced dilution venting before/during workspace entry.",
            "Install prominent safety warning signage at all entryway thresholds.",
            "Test oxygen concentration to confirm > 19.5% before entry."
        ],
        "B-1": [
            "Perform a formal Quantitative Oxygen Deficiency Assessment (ODA).",
            "Provide dedicated mechanical dilution ventilation to guarantee O2 stays > 19.5%.",
            "Install physical restricting orifices to choke maximum flow leaks to manageable rates.",
            "Install continuous fixed Oxygen Deficiency Monitors (ODMs) with strobes/horns."
        ],
        "B-2": [
            "Execute a comprehensive Quantitative ODA evaluating worst-case single point failure.",
            "Install coaxial piping systems or ventilated utility runs to mitigate unnoticeable releases.",
            "Position pneumatic emergency shut-off valves outside the threat area."
        ],
        "C (Cleanrooms)": [
            "Confirm dilution ratio meets standards (>23:1 cleanroom or >15:1 subfab).",
            "Interlock HVAC failure relays with automatic visual/audible building evacuation systems.",
            "Apply comprehensive hazard warning labels along all gas system pipelines."
        ],
        "C (Tubing/Cylinders)": [
            "Certify gas distribution line mechanical fittings to corporate standards.",
            "Choke tubing runs to limit worst-case inaudible releases under 0.235 scfm.",
            "Conduct routine inspections of localized gas cabinetry exhaust lines."
        ],
        "D": [
            "Secure outdoor tank areas with security fencing and locking gates.",
            "Post visible signage highlighting high-volume liquid/gas hazards.",
            "Implement standardized written procedures and cryogenic-grade PPE for bulk refuels."
        ]
    }

    selected_controls = controls_map.get(risk['category'], ["No specialized controls loaded."])
    
    for ctrl in selected_controls:
        st.markdown(f"🔹 **{ctrl}**")

    # Metadata Accordion
    with st.expander("📋 Verified Technical Parameters Archive"):
        st.write(f"**Evaluation Mode:** {unit_system} units")
        st.write(f"**Room Volume:** {data['room_volume']} {units['volume']}")
        st.write(f"**Openness:** {data['room_openness']}% | Barriers: {data['has_barriers']}")
        st.write(f"**HVAC Active:** {data['has_hvac']} | Dedicated Room Flow: {data['room_hvac_flow']} {units['hvacFlow']} (K-Factor: {data['k_factor']})")
        st.write(f"**Normal Release:** {data['has_normal_release']} | Finite Source: {data['has_finite_source']} | SPOF Release: {data['has_spof_release']}")

    st.markdown("---")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("← Modify Risk Classification", use_container_width=True):
            set_step(3)
            st.rerun()
    with btn_col2:
        if st.button("Start New Assessment", type="primary", use_container_width=True):
            set_step(1)
            st.rerun()
