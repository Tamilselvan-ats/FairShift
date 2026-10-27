"""FairShift - Decent Work Platform (UN SDG 8).

A production-ready Streamlit application empowering manual workforces
(construction crews, campus custodial/facility staff) and employers
with multilingual safety reporting, anonymization, timesheet auditing,
fair pay calculation, and workforce analytics.
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Dict, Any, List, Optional
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from config import (
    APP_NAME,
    APP_SUBTITLE,
    APP_VERSION,
    UN_SDG_TARGET,
    SECTOR_CONSTRUCTION,
    SECTOR_COLLEGE,
    SECTOR_GENERAL,
    PRIMARY_MODEL,
    STANDARD_DAILY_HOURS_LIMIT,
    STATUTORY_OVERTIME_MULTIPLIER,
    COLOR_URGENT_BG,
    COLOR_URGENT_BORDER,
    COLOR_URGENT_TEXT,
    COLOR_WARNING_BG,
    COLOR_WARNING_BORDER,
    COLOR_WARNING_TEXT,
    COLOR_ROUTINE_BG,
    COLOR_ROUTINE_BORDER,
    COLOR_ROUTINE_TEXT,
)
from schemas import SafetyFeedbackReport, ShiftScanReport
from pay_calculator import calculate_fair_pay, assess_fatigue_level, normalize_urgency
from ai_service import (
    analyze_safety_feedback,
    analyze_timesheet_data,
    get_gemini_client,
)
from sample_data import (
    PRESET_SAFETY_ROUTINE,
    PRESET_SAFETY_HAZARD,
    PRESET_SAFETY_OVERTIME,
    PRESET_TIMESHEET_CONSTRUCTION,
    PRESET_TIMESHEET_COLLEGE,
    PRESET_TIMESHEET_COMPLIANT,
    get_initial_safety_reports,
    get_initial_shift_records,
)

# Load environment variables safely
load_dotenv()

# Streamlit Page Configuration
st.set_page_config(
    page_title=f"{APP_NAME} | {APP_SUBTITLE}",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
if "safety_reports" not in st.session_state:
    st.session_state.safety_reports = get_initial_safety_reports()

if "shift_records" not in st.session_state:
    st.session_state.shift_records = get_initial_shift_records()

if "active_safety_input" not in st.session_state:
    st.session_state.active_safety_input = ""

if "active_timesheet_input" not in st.session_state:
    st.session_state.active_timesheet_input = ""

if "last_safety_analysis" not in st.session_state:
    st.session_state.last_safety_analysis = None

if "last_shift_analysis" not in st.session_state:
    st.session_state.last_shift_analysis = None


# =====================================================================
# ACCESSIBILITY & STYLING (WCAG 2.1 High Contrast & Touch Targets)
# =====================================================================
def inject_custom_css(high_contrast: bool = False) -> None:
    """Inject custom CSS for high contrast readability and mobile ergonomics.

    Args:
        high_contrast: If True, applies enlarged typography and high-contrast borders.
    """
    font_size = "18px" if high_contrast else "16px"
    border_width = "3px" if high_contrast else "1px"

    css = f"""
    <style>
    /* Global accessibility */
    body {{
        font-size: {font_size};
    }}
    .stButton > button {{
        min-height: 48px;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease-in-out;
    }}
    /* High visual impact alert banners */
    .banner-urgent {{
        background-color: {COLOR_URGENT_BG};
        color: {COLOR_URGENT_TEXT};
        border: 3px solid {COLOR_URGENT_BORDER};
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(220, 38, 38, 0.2);
    }}
    .banner-warning {{
        background-color: {COLOR_WARNING_BG};
        color: {COLOR_WARNING_TEXT};
        border: 3px solid {COLOR_WARNING_BORDER};
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(217, 119, 6, 0.2);
    }}
    .banner-routine {{
        background-color: {COLOR_ROUTINE_BG};
        color: {COLOR_ROUTINE_TEXT};
        border: 3px solid {COLOR_ROUTINE_BORDER};
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(22, 163, 74, 0.2);
    }}
    .report-card {{
        background: #ffffff;
        border: {border_width} solid #e2e8f0;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_audio_readout_widget(text_content: str, label: str = "🔊 Read Out Aloud (Audio Playback)") -> None:
    """Render a simulated browser Web Speech audio readout button for low-literacy users.

    Args:
        text_content: The text to be spoken aloud.
        label: Button display text.
    """
    clean_text = text_content.replace('"', '\\"').replace("\n", " ")
    audio_html = f"""
    <div style="margin-top: 10px; margin-bottom: 10px;">
        <button onclick="
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance('{clean_text}');
                utterance.rate = 0.95;
                window.speechSynthesis.speak(utterance);
            }} else {{
                alert('Audio readout is supported on all modern mobile and desktop browsers.');
            }}
        " style="
            background: #2563eb;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 8px 14px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        ">
            {label}
        </button>
    </div>
    """
    st.markdown(audio_html, unsafe_allow_html=True)


# =====================================================================
# SIDEBAR NAVIGATION & SETTINGS
# =====================================================================
with st.sidebar:
    st.markdown(f"### 🛡️ **{APP_NAME}**")
    st.caption(f"{APP_SUBTITLE} • v{APP_VERSION}")
    st.caption(f"_{UN_SDG_TARGET}_")
    st.divider()

    # Primary View Toggle
    current_view = st.radio(
        "📱 **Select Portal View:**",
        options=["👷 Worker Portal (Mobile Friendly)", "📊 Admin Dashboard (Workforce Analytics)"],
        index=0,
    )

    st.divider()
    st.markdown("#### 🏭 **Sector Filter / Context**")
    selected_sector = st.selectbox(
        "Industry Sector:",
        options=[
            "All Sectors / Cross-Industry",
            SECTOR_CONSTRUCTION,
            SECTOR_COLLEGE,
        ],
        index=0,
        help="Demonstrates targeted safety, ergonomic, and wage policies for manual workforces.",
    )

    st.divider()
    st.markdown("#### ♿ **Accessibility**")
    high_contrast = st.toggle("High Contrast & Large Font Mode", value=False)
    inject_custom_css(high_contrast=high_contrast)

    st.divider()
    # API Key & Engine Health Status
    api_key_env = os.getenv("GEMINI_API_KEY")
    if api_key_env:
        st.success(f"🟢 Gemini API Connected (`{PRIMARY_MODEL}`)", icon="✅")
    else:
        st.info("ℹ️ Offline Heuristic Engine Active (Deterministic Fallback Mode)", icon="🛡️")

    st.caption("Powered by Google Gemini & Pydantic")


# =====================================================================
# INTERFACE 1: WORKER PORTAL
# =====================================================================
def render_worker_portal(active_sector: str) -> None:
    """Render Interface 1: Mobile-friendly worker portal with high visual cues.

    Args:
        active_sector: Currently active sector filter.
    """
    st.title("👷 Worker SafeSpace & FairPay Portal")
    st.markdown(
        "**Confidential, multilingual voice/text reporting & timesheet verification.** "
        "Your identity is automatically protected by the AI Retaliation Shield."
    )

    sector_label = SECTOR_GENERAL if active_sector.startswith("All") else active_sector
    st.info(f"📍 Active Workplace Context: **{sector_label}** | 🔒 **100% Anonymous & Retaliation-Proof**")

    tab_safety, tab_shift = st.tabs([
        "🗣️ Multilingual Safety & Feedback Reporter",
        "⏱️ Shift & Payslip Scanner",
    ])

    # -----------------------------------------------------------------
    # FEATURE 1: MULTILINGUAL SAFETY & FEEDBACK REPORTER
    # -----------------------------------------------------------------
    with tab_safety:
        st.subheader("1. Speak or Type Your Workplace Report")
        st.caption(
            "Enter your report in any language or dialect (Hindi, Spanish, Bengali, Tagalog, English, etc.). "
            "Gemini translates it, extracts urgent safety hazards, and strips away all identifying names."
        )

        st.markdown("**⚡ Quick Demo Presets (1-Click Load):**")
        preset_cols = st.columns(3)

        preset_sector = (
            SECTOR_CONSTRUCTION
            if "Construction" in active_sector
            else (SECTOR_COLLEGE if "College" in active_sector else SECTOR_CONSTRUCTION)
        )

        with preset_cols[0]:
            if st.button("🟢 Preset: Routine Shift", use_container_width=True, help="Load clean safety report"):
                st.session_state.active_safety_input = PRESET_SAFETY_ROUTINE[preset_sector]
                st.session_state.last_safety_analysis = None
                st.rerun()

        with preset_cols[1]:
            if st.button("🔴 Preset: Hazard Report", use_container_width=True, help="Load severe hazard report"):
                st.session_state.active_safety_input = PRESET_SAFETY_HAZARD[preset_sector]
                st.session_state.last_safety_analysis = None
                st.rerun()

        with preset_cols[2]:
            if st.button("🟡 Preset: Unpaid Overtime & Fatigue", use_container_width=True, help="Load exhaustion report"):
                st.session_state.active_safety_input = PRESET_SAFETY_OVERTIME[preset_sector]
                st.session_state.last_safety_analysis = None
                st.rerun()

        user_report_text = st.text_area(
            "Worker Voice Transcription / Message:",
            value=st.session_state.active_safety_input,
            height=140,
            placeholder="Type or dictate: E.g., 'Bhaiya 4th floor pe scaffolding tut gaya hai, Ramesh nearly fell...' or 'Hay fuga de químicos en el sótano...'",
        )

        analyze_col1, analyze_col2 = st.columns([1, 3])
        with analyze_col1:
            analyze_clicked = st.button("🔍 Analyze & Shield Identity", type="primary", use_container_width=True)
        with analyze_col2:
            if st.button("🗑️ Clear Form", use_container_width=False):
                st.session_state.active_safety_input = ""
                st.session_state.last_safety_analysis = None
                st.rerun()

        if analyze_clicked:
            if not user_report_text or not user_report_text.strip():
                st.warning("Please type a report or click one of the 3 Quick Presets above to test.")
            else:
                with st.spinner("🤖 Translating dialect, extracting safety red flags, and anonymizing identity..."):
                    try:
                        analysis_data = analyze_safety_feedback(
                            input_text=user_report_text,
                            selected_sector=sector_label,
                        )
                        st.session_state.last_safety_analysis = analysis_data
                        st.session_state.active_safety_input = user_report_text
                    except Exception as err:
                        st.error(f"Error processing report: {err}")

        # DISPLAY RESULTS WITH PROMINENT VISUAL BANNERS
        res = st.session_state.last_safety_analysis
        if res:
            st.divider()
            urgency = res.get("urgency_level", "routine")

            if urgency == "urgent":
                st.markdown(
                    """
                    <div class="banner-urgent">
                        <h3 style="margin:0 0 8px 0;">🚨 CRITICAL SAFETY HAZARD DETECTED</h3>
                        <p style="margin:0; font-size:16px;">
                            <strong>IMMEDIATE ACTION REQUIRED:</strong> Severe threat to worker safety or life-safety violation identified.
                            Escalation priority logged.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif urgency == "see_soon":
                st.markdown(
                    """
                    <div class="banner-warning">
                        <h3 style="margin:0 0 8px 0;">⚠️ SAFETY NOTICE: ATTENTION REQUIRED</h3>
                        <p style="margin:0; font-size:16px;">
                            <strong>ATTENTION REQUIRED WITHIN 24 HOURS:</strong> Elevated workplace hazard or fatigue pattern reported.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div class="banner-routine">
                        <h3 style="margin:0 0 8px 0;">✅ ROUTINE STATUS REPORT</h3>
                        <p style="margin:0; font-size:16px;">
                            <strong>CONDITIONS STABLE:</strong> Standard maintenance or operational feedback logged.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Details
            c1, c2 = st.columns(2)

            with c1:
                st.markdown("#### 🌐 **English Translation & Summary**")
                st.info(f"**Detected Dialect/Language:** `{res.get('detected_language', 'Auto-detected')}`")
                summary_text = res.get("translated_summary", "No summary generated.")
                st.write(summary_text)

                # Low-literacy accessibility audio button
                render_audio_readout_widget(summary_text, label="🔊 Listen to Summary (Audio Readout)")

                st.markdown("#### 🛡️ **Anonymized Retaliation-Proof Report**")
                st.caption("All personal names, supervisor references, and phone numbers replaced with neutral roles:")
                st.success(res.get("anonymized_report", ""))

            with c2:
                st.markdown("#### 🚩 **Strict Safety Red Flags (Never Invented)**")
                red_flags = res.get("red_flags", [])
                if red_flags:
                    for flag in red_flags:
                        st.markdown(f"- 🔴 **{flag}**")
                else:
                    st.markdown("- 🟢 *No critical physical hazards detected in text.*")

                st.markdown("#### 💤 **Physical Fatigue Assessment**")
                if res.get("fatigue_warning"):
                    st.warning("⚠️ **Fatigue Alert Active:** Worker exhibits extreme exhaustion, dizziness, or shift violations.")
                else:
                    st.write("🟢 *No acute physical fatigue detected.*")

                st.markdown("#### 💡 **Actionable Recommendations**")
                recs = res.get("actionable_recommendations", [])
                if recs:
                    for rec in recs:
                        st.markdown(f"- 📋 {rec}")
                else:
                    st.write("- Routine site monitoring recommended.")

            st.markdown("---")
            if st.button("🚀 Submit to Admin Escalation Queue", type="primary", use_container_width=True):
                new_entry = {
                    "id": f"FS-LIVE-{len(st.session_state.safety_reports) + 101}",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "sector": res.get("sector", sector_label),
                    "detected_language": res.get("detected_language", "English"),
                    "translated_summary": res.get("translated_summary", ""),
                    "anonymized_report": res.get("anonymized_report", ""),
                    "urgency_level": res.get("urgency_level", "routine"),
                    "red_flags": res.get("red_flags", []),
                    "fatigue_warning": res.get("fatigue_warning", False),
                    "confidence": res.get("confidence", "high"),
                    "attrition_risk": res.get("attrition_risk", "low"),
                    "status": "Escalated to Safety Queue",
                    "actionable_recommendations": res.get("actionable_recommendations", []),
                }
                st.session_state.safety_reports.insert(0, new_entry)
                st.success("✅ Report securely sent to Admin Escalation Queue! (Identity 100% confidential).")

    # -----------------------------------------------------------------
    # FEATURE 2: SHIFT & PAYSLIP SCANNER
    # -----------------------------------------------------------------
    with tab_shift:
        st.subheader("2. Scan Messy Timesheet / Payslip Notes")
        st.caption(
            "Upload an image/text note or paste unformatted shift hours. "
            "Gemini structures hours, calculates fair statutory overtime pay (1.5x), and warns of excessive shift fatigue."
        )

        st.markdown("**⚡ Quick Demo Timesheet Presets (1-Click Load):**")
        ts_cols = st.columns(3)

        with ts_cols[0]:
            if st.button("🏗️ Preset: Construction 14.5h Overtime", use_container_width=True):
                st.session_state.active_timesheet_input = PRESET_TIMESHEET_CONSTRUCTION
                st.session_state.last_shift_analysis = None
                st.rerun()

        with ts_cols[1]:
            if st.button("🏫 Preset: College Custodial Night Shift", use_container_width=True):
                st.session_state.active_timesheet_input = PRESET_TIMESHEET_COLLEGE
                st.session_state.last_shift_analysis = None
                st.rerun()

        with ts_cols[2]:
            if st.button("✅ Preset: Compliant 8h Shift", use_container_width=True):
                st.session_state.active_timesheet_input = PRESET_TIMESHEET_COMPLIANT
                st.session_state.last_shift_analysis = None
                st.rerun()

        uploaded_file = st.file_uploader(
            "Upload Timesheet Document (.txt, .csv, log):",
            type=["txt", "csv", "log"],
            help="Upload raw digital punch logs or message exports.",
        )
        if uploaded_file is not None:
            try:
                st.session_state.active_timesheet_input = uploaded_file.read().decode("utf-8")
            except Exception:
                st.warning("Could not read uploaded text file. Please paste text directly below.")

        timesheet_text = st.text_area(
            "Messy Timesheet Notes or Punch Record:",
            value=st.session_state.active_timesheet_input,
            height=140,
            placeholder="E.g., 'Worked Monday 6am-8:30pm (14.5 hrs). Rate is 18/hr. Boss gave 160 cash envelope, deducted 20 for drinking water.'",
        )

        ts_act1, ts_act2 = st.columns([1, 3])
        with ts_act1:
            audit_clicked = st.button("🧮 Audit Shift & Fair Pay", type="primary", use_container_width=True)
        with ts_act2:
            if st.button("🗑️ Clear Timesheet", use_container_width=False):
                st.session_state.active_timesheet_input = ""
                st.session_state.last_shift_analysis = None
                st.rerun()

        if audit_clicked:
            if not timesheet_text or not timesheet_text.strip():
                st.warning("Please enter or load timesheet text above.")
            else:
                with st.spinner("🤖 Auditing hours, statutory overtime rates (1.5x), and fatigue limits..."):
                    try:
                        shift_analysis = analyze_timesheet_data(
                            timesheet_raw_text=timesheet_text,
                            default_sector=sector_label,
                        )
                        st.session_state.last_shift_analysis = shift_analysis
                        st.session_state.active_timesheet_input = timesheet_text
                    except Exception as err:
                        st.error(f"Error auditing timesheet: {err}")

        # DISPLAY SHIFT SCANNER RESULTS
        sres = st.session_state.last_shift_analysis
        if sres:
            st.divider()
            shortfall = sres.get("wage_shortfall", 0.0)
            fatigue_alert = sres.get("fatigue_alert", False)
            fatigue_level = sres.get("fatigue_level", "normal")

            if shortfall > 0 or fatigue_level == "critical":
                st.markdown(
                    f"""
                    <div class="banner-urgent">
                        <h3 style="margin:0 0 6px 0;">🚨 WAGE SHORTFALL & FATIGUE ALERT</h3>
                        <p style="margin:0; font-size:16px;">
                            <strong>Underpayment Identified:</strong> Worker was underpaid by <strong>${shortfall:.2f}</strong>.
                            {' Extreme fatigue hazard (>12h continuous shift).' if fatigue_level == 'critical' else ''}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif fatigue_alert or fatigue_level == "warning":
                st.markdown(
                    """
                    <div class="banner-warning">
                        <h3 style="margin:0 0 6px 0;">⚠️ FATIGUE WARNING: EXTENDED SHIFT</h3>
                        <p style="margin:0; font-size:16px;">
                            Shift exceeds safe 8-hour baseline. Rest interval required before next scheduled shift.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div class="banner-routine">
                        <h3 style="margin:0 0 6px 0;">✅ COMPLIANT SHIFT & FAIR COMPENSATION</h3>
                        <p style="margin:0; font-size:16px;">
                            Hours within statutory limits and pay fully complies with fair labor standards.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            with mcol1:
                st.metric(
                    "Total Hours Logged",
                    f"{sres.get('total_hours_worked', 0.0):.1f} hrs",
                    delta=f"{sres.get('overtime_hours', 0.0):.1f} hrs Overtime",
                    delta_color="inverse" if sres.get("overtime_hours", 0.0) > 0 else "off",
                )
            with mcol2:
                st.metric(
                    "Base / Overtime Rate",
                    f"${sres.get('base_hourly_rate', 0.0):.2f}/hr",
                    help=f"Statutory 1.5x Overtime Rate: ${sres.get('overtime_hourly_rate', 0.0):.2f}/hr",
                )
            with mcol3:
                st.metric(
                    "Fair Expected Pay",
                    f"${sres.get('total_expected_fair_pay', 0.0):.2f}",
                    help="Standard Pay + 1.5x Overtime Pay",
                )
            with mcol4:
                st.metric(
                    "Wage Shortfall (Owed)",
                    f"${shortfall:.2f}",
                    delta=f"-${shortfall:.2f}" if shortfall > 0 else "Fairly Paid",
                    delta_color="inverse" if shortfall > 0 else "normal",
                )

            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown("#### ⚖️ **Fair Labor Pay Breakdown**")
                st.write(f"- **Standard Hours (up to 8h):** {sres.get('standard_hours', 0.0)} hrs → `${sres.get('expected_standard_pay', 0.0):.2f}`")
                st.write(f"- **Overtime Hours (>8h):** {sres.get('overtime_hours', 0.0)} hrs @ 1.5x → `${sres.get('expected_overtime_pay', 0.0):.2f}`")
                st.write(f"- **Actual Compensation Received:** `${sres.get('reported_pay', 0.0):.2f}`")
                st.write(f"- **Role / Shift:** `{sres.get('worker_role', 'Worker')}` ({sres.get('shift_date_or_period', 'Recent')})")

            with sc2:
                st.markdown("#### 💤 **Fatigue & Rest Requirements**")
                fatigue_desc = sres.get("fatigue_reason", "Shift completed safely.")
                st.info(fatigue_desc)
                render_audio_readout_widget(fatigue_desc, label="🔊 Listen to Health Notice")

                st.markdown("#### ⚠️ **Flagged Anomalies**")
                anomalies = sres.get("anomalies", [])
                if anomalies:
                    for a in anomalies:
                        st.markdown(f"- 🔴 **{a}**")
                else:
                    st.write("- 🟢 *No labor anomalies identified.*")

            st.markdown("---")
            if st.button("📥 Log Shift Record to Admin Database", type="primary", use_container_width=True):
                new_shift = {
                    "id": f"TS-LIVE-{len(st.session_state.shift_records) + 95}",
                    "worker_role": sres.get("worker_role", "Worker"),
                    "sector": sres.get("sector", sector_label),
                    "shift_date_or_period": sres.get("shift_date_or_period", "Today"),
                    "total_hours_worked": sres.get("total_hours_worked", 0.0),
                    "standard_hours": sres.get("standard_hours", 0.0),
                    "overtime_hours": sres.get("overtime_hours", 0.0),
                    "base_hourly_rate": sres.get("base_hourly_rate", 15.0),
                    "overtime_hourly_rate": sres.get("overtime_hourly_rate", 22.5),
                    "expected_standard_pay": sres.get("expected_standard_pay", 0.0),
                    "expected_overtime_pay": sres.get("expected_overtime_pay", 0.0),
                    "total_expected_fair_pay": sres.get("total_expected_fair_pay", 0.0),
                    "reported_pay": sres.get("reported_pay", 0.0),
                    "wage_shortfall": sres.get("wage_shortfall", 0.0),
                    "fatigue_alert": sres.get("fatigue_alert", False),
                    "fatigue_level": sres.get("fatigue_level", "normal"),
                    "fatigue_reason": sres.get("fatigue_reason", ""),
                    "anomalies": sres.get("anomalies", []),
                }
                st.session_state.shift_records.insert(0, new_shift)
                st.success("✅ Shift record logged successfully for workforce analytics review!")


# =====================================================================
# INTERFACE 2: ADMIN DASHBOARD (WORKFORCE ANALYTICS & ESCALATION)
# =====================================================================
def render_admin_dashboard(active_sector: str) -> None:
    """Render Interface 2: Desktop-friendly workforce analytics and escalation dashboard.

    Args:
        active_sector: Currently active sector filter.
    """
    st.title("📊 Workforce Analytics & Escalation Command")
    st.markdown(
        "**Real-time monitoring of anonymized worker safety reports, fatigue spikes, and wage shortfalls.** "
        f"Enforcing _{UN_SDG_TARGET}_ across facilities and job sites."
    )

    all_reports = st.session_state.safety_reports
    all_shifts = st.session_state.shift_records

    if not active_sector.startswith("All"):
        filtered_reports = [r for r in all_reports if r.get("sector") == active_sector]
        filtered_shifts = [s for s in all_shifts if s.get("sector") == active_sector]
    else:
        filtered_reports = all_reports
        filtered_shifts = all_shifts

    total_reports_count = len(filtered_reports)
    urgent_count = sum(1 for r in filtered_reports if r.get("urgency_level") == "urgent")
    fatigue_count = sum(1 for r in filtered_reports if r.get("fatigue_warning")) + sum(
        1 for s in filtered_shifts if s.get("fatigue_alert")
    )
    total_shortfall = sum(s.get("wage_shortfall", 0.0) for s in filtered_shifts)
    high_attrition_count = sum(1 for r in filtered_reports if r.get("attrition_risk") == "high")
    attrition_rate = (
        round((high_attrition_count / total_reports_count) * 100, 1) if total_reports_count > 0 else 0.0
    )

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("Total Incident Reports", total_reports_count)
    with k2:
        st.metric("🚨 Critical Red Flags", urgent_count, delta="Immediate Action", delta_color="inverse")
    with k3:
        st.metric("⚠️ Severe Fatigue Alerts", fatigue_count, delta="Accident Risk", delta_color="inverse")
    with k4:
        st.metric("💰 Unpaid Wage Shortfall", f"${total_shortfall:,.2f}", delta="Audit Due", delta_color="inverse")
    with k5:
        st.metric("🚪 Quit / Attrition Risk", f"{attrition_rate}% High", delta="Retention Alert", delta_color="inverse")

    st.divider()

    st.subheader("📈 Workforce Safety & Labor Health Heatmap")
    chart_c1, chart_c2 = st.columns(2)

    with chart_c1:
        st.markdown("**Incident Severity Breakdown**")
        urgency_counts = {
            "Urgent (Life-Safety)": sum(1 for r in filtered_reports if r.get("urgency_level") == "urgent"),
            "See Soon (24h Notice)": sum(1 for r in filtered_reports if r.get("urgency_level") == "see_soon"),
            "Routine Status": sum(1 for r in filtered_reports if r.get("urgency_level") == "routine"),
        }
        df_urgency = pd.DataFrame(list(urgency_counts.items()), columns=["Severity", "Count"]).set_index("Severity")
        st.bar_chart(df_urgency, color=COLOR_URGENT_BORDER)

    with chart_c2:
        st.markdown("**Shift Fatigue Distribution**")
        fatigue_tiers = {
            "Critical (>12h)": sum(1 for s in filtered_shifts if s.get("fatigue_level") == "critical"),
            "Warning (9-12h)": sum(1 for s in filtered_shifts if s.get("fatigue_level") == "warning"),
            "Normal (<=8h)": sum(1 for s in filtered_shifts if s.get("fatigue_level") == "normal"),
        }
        df_fatigue = pd.DataFrame(list(fatigue_tiers.items()), columns=["Fatigue Level", "Shifts"]).set_index("Fatigue Level")
        st.bar_chart(df_fatigue, color=COLOR_WARNING_BORDER)

    st.divider()

    st.subheader("🚨 Incident Escalation Queue & Remediation Tracker")
    st.caption("Inspect anonymized worker testimony, track OSHA/labor violations, and dispatch remediation.")

    if not filtered_reports:
        st.info("No safety reports matching current sector filter.")
    else:
        for idx, report in enumerate(filtered_reports):
            urgency = report.get("urgency_level", "routine")
            urgency_icon = "🔴" if urgency == "urgent" else ("🟡" if urgency == "see_soon" else "🟢")
            sector = report.get("sector", SECTOR_GENERAL)

            expander_title = (
                f"{urgency_icon} [{report.get('id', 'FS')}] {sector} — "
                f"{report.get('translated_summary', 'Worker Report')[:75]}... ({report.get('timestamp', 'Recent')})"
            )

            with st.expander(expander_title, expanded=(urgency == "urgent")):
                dcol1, dcol2 = st.columns([2, 1])

                with dcol1:
                    st.markdown("**🛡️ Anonymized Worker Narrative:**")
                    st.write(report.get("anonymized_report", ""))

                    st.markdown("**🚩 Strictly Extracted Red Flags:**")
                    r_flags = report.get("red_flags", [])
                    if r_flags:
                        for rf in r_flags:
                            st.markdown(f"- 🔴 **{rf}**")
                    else:
                        st.markdown("- 🟢 *No active red flags.*")

                    st.markdown("**💡 Required Management Action:**")
                    for a_rec in report.get("actionable_recommendations", []):
                        st.markdown(f"- 📋 {a_rec}")

                with dcol2:
                    st.markdown("#### Incident Metadata")
                    st.write(f"**Original Language:** `{report.get('detected_language', 'English')}`")
                    st.write(f"**Urgency Level:** `{urgency.upper()}`")
                    st.write(f"**Fatigue Involved:** `{'YES ⚠️' if report.get('fatigue_warning') else 'NO'}`")
                    st.write(f"**Quit / Attrition Risk:** `{report.get('attrition_risk', 'low').upper()}`")
                    st.write(f"**Current Status:** `{report.get('status', 'Pending')}`")

                    st.markdown("**Escalation Dispatch:**")
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("🚨 Dispatch Inspector", key=f"disp_{idx}"):
                            report["status"] = "Inspector Dispatched"
                            st.success("Inspector dispatched to site.")
                            st.rerun()
                    with btn_col2:
                        if st.button("✅ Mark Resolved", key=f"res_{idx}"):
                            report["status"] = "Resolved & Archived"
                            st.info("Marked as resolved.")
                            st.rerun()

    st.divider()

    st.subheader("💵 Shift & Payroll Audit Log")
    st.caption("Verifying standard hours, 1.5x statutory overtime rates, and wage restitution.")

    if filtered_shifts:
        table_rows = []
        for s in filtered_shifts:
            table_rows.append({
                "Record ID": s.get("id"),
                "Sector": s.get("sector"),
                "Role": s.get("worker_role"),
                "Total Hours": f"{s.get('total_hours_worked', 0.0):.1f}h",
                "Overtime": f"{s.get('overtime_hours', 0.0):.1f}h",
                "Base Rate": f"${s.get('base_hourly_rate', 0.0):.2f}",
                "Fair Pay Due": f"${s.get('total_expected_fair_pay', 0.0):.2f}",
                "Reported Paid": f"${s.get('reported_pay', 0.0):.2f}",
                "Shortfall (Owed)": f"${s.get('wage_shortfall', 0.0):.2f}",
                "Fatigue Level": s.get("fatigue_level", "normal").upper(),
            })
        df_shifts = pd.DataFrame(table_rows)
        st.dataframe(df_shifts, use_container_width=True)

        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            csv_data = df_shifts.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Wage Remediation Audit (CSV)",
                data=csv_data,
                file_name="fairshift_payroll_audit.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with exp_col2:
            json_data = json.dumps(filtered_shifts, indent=2).encode("utf-8")
            st.download_button(
                label="📥 Export Full Audit Log (JSON)",
                data=json_data,
                file_name="fairshift_audit_log.json",
                mime="application/json",
                use_container_width=True,
            )
    else:
        st.info("No shift records matching current sector filter.")


# =====================================================================
# MAIN ROUTING
# =====================================================================
def main() -> None:
    """Main application entrypoint routing based on sidebar selection."""
    if "Worker Portal" in current_view:
        render_worker_portal(selected_sector)
    else:
        render_admin_dashboard(selected_sector)


if __name__ == "__main__":
    main()
