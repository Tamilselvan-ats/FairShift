"""FairShift - Strict Pydantic Schemas for Deterministic AI Outputs.

Defines BaseModel classes used as Gemini response_schemas with custom
field validators to guarantee deterministic JSON parsing, type safety,
and data normalization across the entire application.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class SafetyFeedbackReport(BaseModel):
    """Structured safety report extracted from multilingual worker voice/text submissions."""

    translated_summary: str = Field(
        ...,
        description="Clear, plain English translation and concise summary of the worker's report.",
        min_length=3,
    )
    anonymized_report: str = Field(
        ...,
        description=(
            "The narrative report with all personal identifying details (names, phone numbers, "
            "specific worker IDs, supervisor identities) completely removed or replaced with neutral roles "
            "(e.g., 'Worker A', 'Site Supervisor') to prevent retaliation."
        ),
        min_length=3,
    )
    urgency_level: Literal["routine", "see_soon", "urgent"] = Field(
        ...,
        description="Severity classification: 'routine' (minor), 'see_soon' (needs attention <24h), 'urgent' (critical life-safety).",
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="Specific safety hazards or labor rights violations strictly extracted from the input text. Never hallucinated or invented.",
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
        description="Assessed risk of the worker quitting, walking off the job, or experiencing burnout.",
    )
    actionable_recommendations: List[str] = Field(
        default_factory=list,
        description="Concrete, practical safety or administrative actions management must take.",
    )

    @field_validator("urgency_level", mode="before")
    @classmethod
    def normalize_urgency_input(cls, v: str) -> str:
        """Normalize case and whitespace for urgency level."""
        if not v:
            return "routine"
        cleaned = str(v).strip().lower()
        if any(term in cleaned for term in ["urgent", "critical", "danger", "emergency", "red", "immediate"]):
            return "urgent"
        elif any(term in cleaned for term in ["see_soon", "warning", "caution", "soon", "moderate", "yellow"]):
            return "see_soon"
        return "routine"

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: str) -> str:
        """Normalize confidence level to standard literals."""
        if not v:
            return "medium"
        cleaned = str(v).strip().lower()
        if cleaned in ["low", "medium", "high"]:
            return cleaned
        return "medium"

    @field_validator("red_flags", mode="before")
    @classmethod
    def sanitize_red_flags(cls, v: Optional[List[str]]) -> List[str]:
        """Deduplicate and strip whitespace from red flag entries."""
        if not v:
            return []
        cleaned_flags = []
        for item in v:
            if item and isinstance(item, str):
                s = item.strip()
                if s and s not in cleaned_flags:
                    cleaned_flags.append(s)
        return cleaned_flags


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
        description="Regular non-overtime hours (typically up to 8.0 hours/day).",
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
        description="Actual pay or cash compensation the worker received or was promised.",
    )
    wage_shortfall: float = Field(
        ...,
        description="Difference between fair expected pay and reported pay. Positive indicates underpayment/wage theft.",
    )
    fatigue_alert: bool = Field(
        ...,
        description="True if shift duration or frequency exceeds safe physiological limits (e.g. >9h/shift).",
    )
    fatigue_level: Literal["normal", "warning", "critical"] = Field(
        default="normal",
        description="Fatigue severity: 'normal' (<=8h), 'warning' (8.5-12h), 'critical' (>12h).",
    )
    fatigue_reason: str = Field(
        default="",
        description="Detailed ergonomic/medical explanation of fatigue danger and mandated rest duration.",
    )
    anomalies: List[str] = Field(
        default_factory=list,
        description="Discrepancies identified, such as missing break logging, off-the-clock work, or improper deductions.",
    )
    sector: Literal["Construction Sites", "College Support & Facility Staff", "General"] = Field(
        default="General",
        description="The workplace sector identified from the timesheet.",
    )

    @model_validator(mode="after")
    def validate_payroll_consistency(self) -> "ShiftScanReport":
        """Verify mathematical relationships and guarantee non-negative wage shortfall."""
        # Ensure total hours equals standard + overtime
        calculated_total = round(self.standard_hours + self.overtime_hours, 2)
        if abs(self.total_hours_worked - calculated_total) > 0.1:
            self.total_hours_worked = calculated_total

        # Ensure expected pay is sum of standard and overtime
        expected_sum = round(self.expected_standard_pay + self.expected_overtime_pay, 2)
        if abs(self.total_expected_fair_pay - expected_sum) > 0.1:
            self.total_expected_fair_pay = expected_sum

        # Calculate wage shortfall accurately
        shortfall = round(max(0.0, self.total_expected_fair_pay - self.reported_pay), 2)
        self.wage_shortfall = shortfall
        return self
