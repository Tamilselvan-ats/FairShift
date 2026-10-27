"""FairShift - Pure Mathematical and Algorithmic Logic for Payroll and Safety Compliance.

Provides deterministic functions for calculating standard/overtime pay, wage shortfalls,
fatigue assessments, and urgency normalization. Decoupled from Streamlit UI to allow
comprehensive unit testing with pytest.
"""

import re
from typing import Dict, Any, Tuple


def calculate_fair_pay(
    total_hours: float,
    base_rate: float,
    reported_pay: float = 0.0,
    standard_day_limit: float = 8.0,
    overtime_multiplier: float = 1.5,
) -> Dict[str, float]:
    """Calculate fair wage, overtime compensation, and identify wage shortfalls.

    Args:
        total_hours: Total hours worked in shift.
        base_rate: Agreed hourly wage rate.
        reported_pay: Compensation paid or offered by employer.
        standard_day_limit: Regular hours limit before overtime triggers (default: 8.0h).
        overtime_multiplier: Multiplier for overtime hours (default: 1.5x).

    Returns:
        Dictionary containing breakdown of hours, rates, expected pay, and wage shortfall.
    """
    total_hours = max(0.0, float(total_hours))
    base_rate = max(0.0, float(base_rate))
    reported_pay = max(0.0, float(reported_pay))

    standard_hours = min(total_hours, standard_day_limit)
    overtime_hours = max(0.0, total_hours - standard_day_limit)

    overtime_rate = round(base_rate * overtime_multiplier, 2)
    expected_standard_pay = round(standard_hours * base_rate, 2)
    expected_overtime_pay = round(overtime_hours * overtime_rate, 2)
    total_expected_pay = round(expected_standard_pay + expected_overtime_pay, 2)

    # Wage shortfall is positive when worker was underpaid
    wage_shortfall = round(max(0.0, total_expected_pay - reported_pay), 2)

    return {
        "total_hours": round(total_hours, 2),
        "standard_hours": round(standard_hours, 2),
        "overtime_hours": round(overtime_hours, 2),
        "base_rate": round(base_rate, 2),
        "overtime_rate": overtime_rate,
        "expected_standard_pay": expected_standard_pay,
        "expected_overtime_pay": expected_overtime_pay,
        "total_expected_pay": total_expected_pay,
        "reported_pay": round(reported_pay, 2),
        "wage_shortfall": wage_shortfall,
    }


def assess_fatigue_level(shift_hours: float) -> Tuple[str, bool, str]:
    """Assess physical fatigue risk based on shift length.

    Args:
        shift_hours: Duration of continuous or single-day shift in hours.

    Returns:
        Tuple of (fatigue_level, fatigue_alert_boolean, detailed_reason).
    """
    shift_hours = max(0.0, float(shift_hours))

    if shift_hours > 12.0:
        return (
            "critical",
            True,
            f"CRITICAL FATIGUE HAZARD: {shift_hours:.1f} hours worked continuously. Extreme risk of motor lapses, heat syncope, and heavy machinery accidents. Mandatory 12+ hour rest required.",
        )
    elif shift_hours > 9.0:
        return (
            "warning",
            True,
            f"MODERATE FATIGUE WARNING: {shift_hours:.1f} hours exceeds 8-hour daily safety limit. Reaction times decrease by up to 40% after 9 hours of manual labor.",
        )
    else:
        return (
            "normal",
            False,
            f"NORMAL SHIFT: {shift_hours:.1f} hours conforms to standard labor safety thresholds.",
        )


def normalize_urgency(val: Any) -> str:
    """Normalize various string forms into strict literal: 'routine', 'see_soon', or 'urgent'."""
    if not val:
        return "routine"

    v = str(val).strip().lower()
    if any(k in v for k in ["urgent", "critical", "emergency", "danger", "hazard", "immediate", "red"]):
        return "urgent"
    elif any(k in v for k in ["see_soon", "warning", "caution", "medium", "soon", "moderate", "yellow"]):
        return "see_soon"
    return "routine"


def scrub_personal_identifiers(text: str) -> str:
    """Sanitize text to redact telephone numbers, email addresses, and employee IDs."""
    if not text:
        return ""

    # Redact phone numbers (various formats)
    sanitized = re.sub(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "[PHONE REDACTED]", text)
    # Redact email addresses
    sanitized = re.sub(r"[\w.-]+@[\w.-]+\.\w+", "[EMAIL REDACTED]", sanitized)
    # Redact Employee ID patterns like ID#1234 or EmpID: 5592
    sanitized = re.sub(r"(?i)\b(id|emp\s*id|worker\s*id|badge)[\s#:]+\w+", "[ID REDACTED]", sanitized)

    return sanitized
