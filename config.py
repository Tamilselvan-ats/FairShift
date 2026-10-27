"""FairShift - Configuration and Domain Constants.

Centralizes all application configurations, OSHA labor thresholds,
AI model cascade settings, and WCAG accessibility standards.
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Application Metadata
APP_NAME: str = "FairShift"
APP_SUBTITLE: str = "Decent Work Platform (UN SDG 8)"
APP_VERSION: str = "2.5.0"

# Target UN Sustainable Development Goal
UN_SDG_TARGET: str = "UN SDG 8.8: Protect labour rights and promote safe and secure working environments"

# Supported Sectors
SECTOR_CONSTRUCTION: str = "Construction Sites"
SECTOR_COLLEGE: str = "College Support & Facility Staff"
SECTOR_GENERAL: str = "General"
ALL_SECTORS: List[str] = [SECTOR_CONSTRUCTION, SECTOR_COLLEGE, SECTOR_GENERAL]

# Labor Standards & Ergonomic Thresholds (OSHA & Statutory Overtime)
STANDARD_DAILY_HOURS_LIMIT: float = 8.0
FATIGUE_WARNING_THRESHOLD_HOURS: float = 9.0
FATIGUE_CRITICAL_THRESHOLD_HOURS: float = 12.0
STATUTORY_OVERTIME_MULTIPLIER: float = 1.5
DEFAULT_MINIMUM_WAGE_BASELINE: float = 15.00

# AI Configuration (google-genai SDK)
PRIMARY_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
FALLBACK_MODELS: List[str] = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]
GEMINI_TEMPERATURE: float = 0.1

# High-Contrast WCAG 2.1 AA Palette
COLOR_URGENT_BG: str = "#fee2e2"
COLOR_URGENT_BORDER: str = "#dc2626"
COLOR_URGENT_TEXT: str = "#991b1b"

COLOR_WARNING_BG: str = "#fef3c7"
COLOR_WARNING_BORDER: str = "#d97706"
COLOR_WARNING_TEXT: str = "#92400e"

COLOR_ROUTINE_BG: str = "#dcfce7"
COLOR_ROUTINE_BORDER: str = "#16a34a"
COLOR_ROUTINE_TEXT: str = "#166534"
