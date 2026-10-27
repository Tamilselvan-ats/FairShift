"""FairShift - Pydantic Schemas for Deterministic AI Outputs.

Defines strict models used as Gemini response_schemas to guarantee
deterministic JSON parsing and type-safety across the application.
"""

from typing import List, Literal
from pydantic import BaseModel, Field


class SafetyFeedbackReport(BaseModel):
    """Structured report extracted from multilingual worker safety/feedback submissions."""

    translated_summary: str = Field(
        ...,
        description="Clear, plain English translation and concise summary of the worker's report.",
    )
    anonymized_report: str = Field(
        ...,
        description=(
            "The narrative report with all personal identifying details (names, phone numbers, "
            "specific worker IDs, supervisor identities) completely removed or replaced with neutral roles "
            "(e.g., 'Worker A', 'Site Supervisor') to prevent retaliation."
        ),
    )
    urgency_level: Literal["routine", "see_soon", "urgent"] = Field(
        ...,
        description="Severity classification: 'routine' for normal updates/minor requests, 'see_soon' for moderate concerns needing attention, 'urgent' for immediate safety risks or severe violations.",
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="Specific safety hazards or labor rights violations strictly extracted from the input text. Never hallucinate or invent flags.",
    )
    fatigue_warning: bool = Field(
        ...,
        description="True if the report indicates extreme physical exhaustion, dizzy spells, lack of mandatory rest breaks, or dangerous consecutive hours.",
    )
    confidence: Literal["low", "medium", "high"] = Field(
        ...,
        description="AI confidence level in translation and entity extraction.",
    )
    detected_language: str = Field(
        default="English",
        description="The primary language or dialect detected in the original voice/text input.",
    )
    sector: Literal["Construction Sites", "College Support & Facility Staff", "General"] = Field(
        default="General",
        description="The workplace sector identified from the context.",
    )
    attrition_risk: Literal["low", "medium", "high"] = Field(
        default="low",
        description="Assessed risk of the worker quitting, walking off the job, or burnout.",
    )
    actionable_recommendations: List[str] = Field(
        default_factory=list,
        description="Concrete, practical safety or administrative actions management must take.",
    )


class ShiftScanReport(BaseModel):
    """Structured payroll and shift analysis extracted from messy timesheets or payslip notes."""

    worker_role: str = Field(
        default="Manual Laborer",
        description="Identified worker role (e.g., Scaffolder, Custodian, Grounds Crew, Equipment Operator).",
    )
    shift_date_or_period: str = Field(
        default="Recent Shift",
        description="Date or shift timeframe mentioned in the submission.",
    )
    total_hours_worked: float = Field(
        ...,
        ge=0.0,
        description="Total hours worked across the reported shift period.",
    )
    standard_hours: float = Field(
        ...,
        ge=0.0,
        description="Regular non-overtime hours (typically up to 8 hours/day or standard baseline).",
    )
    overtime_hours: float = Field(
        ...,
        ge=0.0,
        description="Hours worked in excess of regular hours.",
    )
    base_hourly_rate: float = Field(
        ...,
        ge=0.0,
        description="Agreed or standard base hourly wage rate in currency units.",
    )
    overtime_hourly_rate: float = Field(
        ...,
        ge=0.0,
        description="Overtime hourly rate (standardly 1.5x base hourly rate).",
    )
    expected_standard_pay: float = Field(
        ...,
        ge=0.0,
        description="Calculated fair base pay (standard_hours * base_hourly_rate).",
    )
    expected_overtime_pay: float = Field(
        ...,
        ge=0.0,
        description="Calculated fair overtime pay (overtime_hours * overtime_hourly_rate).",
    )
    total_expected_fair_pay: float = Field(
        ...,
        ge=0.0,
        description="Sum of standard pay and overtime pay that the worker earned.",
    )
    reported_pay: float = Field(
        ...,
        ge=0.0,
        description="Actual pay or cash compensation the worker received or was told they would receive.",
    )
    wage_shortfall: float = Field(
        ...,
        description="Difference between fair expected pay and reported pay. Positive indicates wage underpayment/theft.",
    )
    fatigue_alert: bool = Field(
        ...,
        description="True if shift duration or frequency exceeds safe physiological limits (e.g. >10h/shift or continuous night shifts).",
    )
    fatigue_level: Literal["normal", "warning", "critical"] = Field(
        default="normal",
        description="Fatigue severity: 'normal' (<=8h), 'warning' (8.5-12h), 'critical' (>12h or sleepless double shifts).",
    )
    fatigue_reason: str = Field(
        default="",
        description="Detailed medical/ergonomic explanation of fatigue danger and mandated rest duration.",
    )
    anomalies: List[str] = Field(
        default_factory=list,
        description="Discrepancies identified, such as missing break logging, off-the-clock work, or improper deductions.",
    )
    sector: Literal["Construction Sites", "College Support & Facility Staff", "General"] = Field(
        default="General",
        description="The workplace sector identified from the timesheet.",
    )
