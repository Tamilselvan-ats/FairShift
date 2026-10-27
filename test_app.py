"""FairShift - Unit Test Suite for Pytest.

Verifies non-UI core functions required by the Hack2Skill evaluation metric:
1. Pydantic JSON schema parsing & deterministic validation
2. Urgency level normalization and safety heuristics
3. Fair pay, statutory overtime, and wage shortfall calculations
4. Physical fatigue threshold assessments
5. Personal identifier scrubbing
"""

import pytest
from pydantic import ValidationError

from schemas import SafetyFeedbackReport, ShiftScanReport
from pay_calculator import (
    calculate_fair_pay,
    assess_fatigue_level,
    normalize_urgency,
    scrub_personal_identifiers,
)


def test_safety_feedback_pydantic_schema_validation():
    """Verify SafetyFeedbackReport schema enforces required fields and types."""
    valid_data = {
        "translated_summary": "Scaffolding snapped on the 4th floor; fall hazard.",
        "anonymized_report": "Worker reported broken scaffolding board at 30ft.",
        "urgency_level": "urgent",
        "red_flags": ["Broken scaffolding plank", "Missing safety harness"],
        "fatigue_warning": True,
        "confidence": "high",
        "detected_language": "Hindi",
        "sector": "Construction Sites",
        "attrition_risk": "high",
        "actionable_recommendations": ["Halt work immediately", "Issue harnesses"],
    }

    report = SafetyFeedbackReport(**valid_data)
    assert report.urgency_level == "urgent"
    assert report.fatigue_warning is True
    assert len(report.red_flags) == 2
    assert report.confidence == "high"

    # Verify JSON serialization & deterministic re-parsing
    json_str = report.model_dump_json()
    reparsed = SafetyFeedbackReport.model_validate_json(json_str)
    assert reparsed.translated_summary == valid_data["translated_summary"]
    assert reparsed.urgency_level == "urgent"

    # Verify that an invalid urgency level raises ValidationError
    invalid_data = valid_data.copy()
    invalid_data["urgency_level"] = "catastrophic"  # Not in allowed literal
    with pytest.raises(ValidationError):
        SafetyFeedbackReport(**invalid_data)


def test_shift_scan_pydantic_schema_validation():
    """Verify ShiftScanReport schema enforces valid hours and calculations."""
    valid_shift = {
        "worker_role": "Dorm Custodian",
        "shift_date_or_period": "2026-10-25",
        "total_hours_worked": 14.0,
        "standard_hours": 8.0,
        "overtime_hours": 6.0,
        "base_hourly_rate": 16.5,
        "overtime_hourly_rate": 24.75,
        "expected_standard_pay": 132.0,
        "expected_overtime_pay": 148.5,
        "total_expected_fair_pay": 280.5,
        "reported_pay": 132.0,
        "wage_shortfall": 148.5,
        "fatigue_alert": True,
        "fatigue_level": "critical",
        "fatigue_reason": "14-hour shift without rest.",
        "anomalies": ["6 unpaid overtime hours"],
        "sector": "College Support & Facility Staff",
    }

    shift_report = ShiftScanReport(**valid_shift)
    assert shift_report.total_hours_worked == 14.0
    assert shift_report.wage_shortfall == 148.5
    assert shift_report.fatigue_alert is True
    assert shift_report.fatigue_level == "critical"

    # Negative hours should fail validation
    invalid_shift = valid_shift.copy()
    invalid_shift["total_hours_worked"] = -5.0
    with pytest.raises(ValidationError):
        ShiftScanReport(**invalid_shift)


def test_pay_calculation_and_overtime_math():
    """Verify mathematical precision of fair pay, 1.5x overtime, and wage shortfalls."""
    # Test 1: Heavy overtime shift (14.5 hours @ $18/hr, paid only $160 cash)
    result = calculate_fair_pay(
        total_hours=14.5,
        base_rate=18.0,
        reported_pay=160.0,
        standard_day_limit=8.0,
        overtime_multiplier=1.5,
    )
    assert result["standard_hours"] == 8.0
    assert result["overtime_hours"] == 6.5
    assert result["overtime_rate"] == 27.0  # 18 * 1.5
    assert result["expected_standard_pay"] == 144.0  # 8 * 18
    assert result["expected_overtime_pay"] == 175.5  # 6.5 * 27
    assert result["total_expected_pay"] == 319.5
    assert result["wage_shortfall"] == 159.5  # 319.5 - 160.0

    # Test 2: Standard compliant 8-hour shift (@ $20/hr, paid $160)
    result_compliant = calculate_fair_pay(
        total_hours=8.0,
        base_rate=20.0,
        reported_pay=160.0,
    )
    assert result_compliant["standard_hours"] == 8.0
    assert result_compliant["overtime_hours"] == 0.0
    assert result_compliant["expected_overtime_pay"] == 0.0
    assert result_compliant["total_expected_pay"] == 160.0
    assert result_compliant["wage_shortfall"] == 0.0

    # Test 3: Zero hours worked
    result_zero = calculate_fair_pay(total_hours=0.0, base_rate=15.0, reported_pay=0.0)
    assert result_zero["total_expected_pay"] == 0.0
    assert result_zero["wage_shortfall"] == 0.0

    # Test 4: Overpaid worker should have 0 shortfall (never negative)
    result_overpaid = calculate_fair_pay(total_hours=8.0, base_rate=15.0, reported_pay=200.0)
    assert result_overpaid["wage_shortfall"] == 0.0


def test_fatigue_assessment_rules():
    """Verify fatigue danger tiers (normal, warning, critical)."""
    # Critical fatigue (>12 hours)
    crit_level, crit_alert, crit_reason = assess_fatigue_level(14.5)
    assert crit_level == "critical"
    assert crit_alert is True
    assert "CRITICAL FATIGUE HAZARD" in crit_reason

    # Warning fatigue (8.5 - 12 hours)
    warn_level, warn_alert, warn_reason = assess_fatigue_level(10.5)
    assert warn_level == "warning"
    assert warn_alert is True
    assert "MODERATE FATIGUE WARNING" in warn_reason

    # Normal shift (<= 8 hours)
    norm_level, norm_alert, norm_reason = assess_fatigue_level(8.0)
    assert norm_level == "normal"
    assert norm_alert is False
    assert "NORMAL SHIFT" in norm_reason


def test_urgency_normalization():
    """Verify robust normalization of arbitrary urgency text."""
    assert normalize_urgency("Urgent Hazard!") == "urgent"
    assert normalize_urgency("EMERGENCY DANGER") == "urgent"
    assert normalize_urgency("CRITICAL") == "urgent"
    assert normalize_urgency("see_soon") == "see_soon"
    assert normalize_urgency("Caution needed") == "see_soon"
    assert normalize_urgency("Moderate Warning") == "see_soon"
    assert normalize_urgency("routine") == "routine"
    assert normalize_urgency("All good") == "routine"
    assert normalize_urgency(None) == "routine"


def test_personal_identifier_scrubbing():
    """Verify regex sanitization redacts phone numbers, emails, and worker IDs."""
    raw_text = (
        "My name is John Doe, phone +1 (555) 234-5678, email john.doe@site.org. "
        "Worker ID: 94812 reported the cracked foundation."
    )
    scrubbed = scrub_personal_identifiers(raw_text)
    assert "+1 (555) 234-5678" not in scrubbed
    assert "john.doe@site.org" not in scrubbed
    assert "ID: 94812" not in scrubbed
    assert "[PHONE REDACTED]" in scrubbed
    assert "[EMAIL REDACTED]" in scrubbed
    assert "[ID REDACTED]" in scrubbed
