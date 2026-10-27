"""FairShift - AI Service Layer with Gemini API, Pydantic Schema, and Token Caching.

Integrates with the `google-genai` SDK using `gemini-2.5-flash`.
Applies @st.cache_data to maximize token efficiency and prevent redundant processing.
"""

import json
import os
from typing import Dict, Any, Optional
import streamlit as st
from dotenv import load_dotenv

from schemas import SafetyFeedbackReport, ShiftScanReport
from pay_calculator import calculate_fair_pay, assess_fatigue_level, normalize_urgency

# Load environment variables safely
load_dotenv()

# Priority model list: Primary requirement is gemini-2.5-flash, with resilient fallbacks
PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]


def get_gemini_client():
    """Retrieve an authenticated google-genai Client or None if API key is missing.

    Strictly reads GEMINI_API_KEY from environment without exposing or writing keys.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as exc:
        st.error(f"Failed to initialize Gemini Client: {exc}")
        return None


def execute_gemini_call(
    prompt: str,
    response_schema: Any,
    system_instruction: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute a structured content generation call with primary gemini-2.5-flash and fallbacks."""
    client = get_gemini_client()
    if not client:
        raise ValueError("GEMINI_API_KEY environment variable is missing or empty.")

    from google.genai import types

    models_to_try = [PRIMARY_MODEL] + FALLBACK_MODELS
    last_error = None

    for model_name in models_to_try:
        try:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1,  # Low temperature for deterministic analysis
            )
            if system_instruction:
                config.system_instruction = system_instruction

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )

            # Deterministic JSON verification using Pydantic
            raw_text = response.text.strip()
            parsed_model = response_schema.model_validate_json(raw_text)
            return parsed_model.model_dump()
        except Exception as exc:
            last_error = exc
            # If model is deprecated (404) or temporarily overloaded (503), try next fallback
            continue

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")


@st.cache_data(show_spinner=False)
def analyze_safety_feedback(input_text: str, selected_sector: str = "General") -> Dict[str, Any]:
    """Analyze worker feedback or safety hazard reports using Gemini 2.5 Flash.

    Cached via @st.cache_data to save tokens and prevent duplicate API processing.
    """
    if not input_text or not input_text.strip():
        raise ValueError("Input text cannot be empty.")

    system_instruction = (
        "You are FairShift AI, an objective safety auditor and worker rights guardian "
        "supporting UN Sustainable Development Goal 8 (Decent Work and Economic Growth). "
        "Your task is to protect vulnerable manual laborers (e.g. construction crews, college facility/custodial staff). "
        "You must:\n"
        "1. Translate any language/dialect (Hindi, Spanish, Tagalog, colloquial slang, mixed phrases) into clear English.\n"
        "2. Strictly ANONYMIZE the worker and all persons mentioned. Strip out worker names, supervisor names, phone numbers, "
        "and specific badge IDs. Refer to them neutrally as 'Worker', 'Site Supervisor', or 'Facility Manager' to guarantee non-retaliation.\n"
        "3. Extract ONLY factual, stated safety red flags. NEVER invent, exaggerate, or hallucinate hazards.\n"
        "4. Assign urgency_level strictly: 'routine' (minor update/tool request), 'see_soon' (needs inspection within 24h), "
        "or 'urgent' (immediate danger to life/limb, imminent fall, toxic chemical exposure without PPE, electrical hazard, violence).\n"
        "5. Flag fatigue_warning if worker reports dizziness, double shifts, exhaustion, heat syncope, or denied breaks.\n"
        "6. Provide constructive, practical recommendations for management."
    )

    user_prompt = f"""Sector Context: {selected_sector}

Worker's Voice / Report text:
\"\"\"
{input_text.strip()}
\"\"\"

Analyze this report and return the structured JSON strictly adhering to the schema.
Ensure urgency_level is one of ['routine', 'see_soon', 'urgent'].
Ensure confidence is one of ['low', 'medium', 'high'].
Ensure sector is one of ['Construction Sites', 'College Support & Facility Staff', 'General'].
Ensure attrition_risk is one of ['low', 'medium', 'high']."""

    result = execute_gemini_call(
        prompt=user_prompt,
        response_schema=SafetyFeedbackReport,
        system_instruction=system_instruction,
    )

    # Secondary normalization safety check
    result["urgency_level"] = normalize_urgency(result.get("urgency_level", "routine"))
    return result


@st.cache_data(show_spinner=False)
def analyze_timesheet_data(timesheet_raw_text: str, default_sector: str = "General") -> Dict[str, Any]:
    """Parse messy timesheet / payslip notes into structured hours and fair pay calculations.

    Cached via @st.cache_data for token efficiency.
    """
    if not timesheet_raw_text or not timesheet_raw_text.strip():
        raise ValueError("Timesheet input cannot be empty.")

    system_instruction = (
        "You are FairShift AI's Payroll Auditor enforcing fair wage standards and safe work hours. "
        "Your task is to parse messy, hand-written, or informally recorded worker timesheets, messages, or payslip notes. "
        "Extract: worker_role, shift_date_or_period, total_hours_worked, standard_hours (up to 8h/day), overtime_hours (>8h), "
        "base_hourly_rate (if not stated, assume prevailing minimum standard 15.00/hr), reported_pay (actual pay received or promised). "
        "Overtime hourly rate must be 1.5 times the base hourly rate. "
        "Flag fatigue_alert as True if single shift exceeds 9 hours. "
        "Identify any anomalies such as unpaid overtime, missing lunch breaks, or illegal deductions."
    )

    user_prompt = f"""Workplace Context: {default_sector}

Raw Worker Timesheet Notes / Payslip text:
\"\"\"
{timesheet_raw_text.strip()}
\"\"\"

Parse the timesheet data into the structured ShiftScanReport JSON schema.
Calculate expected fair pay accurately."""

    result = execute_gemini_call(
        prompt=user_prompt,
        response_schema=ShiftScanReport,
        system_instruction=system_instruction,
    )

    # Double check calculations deterministically via pay_calculator
    calc = calculate_fair_pay(
        total_hours=result.get("total_hours_worked", 0.0),
        base_rate=result.get("base_hourly_rate", 15.0),
        reported_pay=result.get("reported_pay", 0.0),
    )
    fatigue_lvl, fatigue_bool, fatigue_reason = assess_fatigue_level(result.get("total_hours_worked", 0.0))

    # Reconcile AI extraction with deterministic arithmetic
    result["standard_hours"] = calc["standard_hours"]
    result["overtime_hours"] = calc["overtime_hours"]
    result["overtime_hourly_rate"] = calc["overtime_rate"]
    result["expected_standard_pay"] = calc["expected_standard_pay"]
    result["expected_overtime_pay"] = calc["expected_overtime_pay"]
    result["total_expected_fair_pay"] = calc["total_expected_pay"]
    result["wage_shortfall"] = calc["wage_shortfall"]

    if fatigue_bool:
        result["fatigue_alert"] = True
        result["fatigue_level"] = fatigue_lvl
        if not result.get("fatigue_reason"):
            result["fatigue_reason"] = fatigue_reason

    return result
