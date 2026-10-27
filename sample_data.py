"""FairShift - Seed Data and Quick Presets for Demo and Live Testing.

Provides presets for the 1-click Worker Portal tests and initial records
for the Admin Analytics Dashboard, covering both Construction Sites and
College Support & Facility Staff sectors (UN SDG 8).
"""

from typing import List, Dict, Any

# =====================================================================
# WORKER PORTAL: SAFETY & FEEDBACK QUICK PRESETS
# =====================================================================

PRESET_SAFETY_ROUTINE = {
    "title": "Routine Shift",
    "icon": "🟢",
    "description": "Standard daily status report with clean safety adherence.",
    "Construction Sites": (
        "Good morning. Shift completed on Sector 4 foundation footing. All 6 crew members "
        "wore hard hats, steel-toe boots, and high-visibility vests. Rebar cages tied safely. "
        "Need 4 additional hand trowels and 2 replacement tape measures for tomorrow morning."
    ),
    "College Support & Facility Staff": (
        "Completed evening custodial sweep across Science Hall floors 1 through 3. "
        "All trash emptied, recycling sorted, and hallway floors buffed. Restocked disinfectant "
        "wipes and soap dispensers. Eyewash stations inspected and logged green. No safety issues."
    ),
}

PRESET_SAFETY_HAZARD = {
    "title": "Hazard Report",
    "icon": "🔴",
    "description": "Immediate safety red flag with worker names and dangerous conditions.",
    "Construction Sites": (
        "Bhaiya fourth floor pe scaffolding ka wood plank toot gaya hai! Ramesh almost fell down today "
        "from 35 feet height! Supervisor Vikram told us 'jaldi kaam karo' and wouldn't give us safety harnesses. "
        "Exposed live 440V cables are also dangling near wet puddles near the concrete mixer. "
        "Someone will die if this is not stopped immediately!"
    ),
    "College Support & Facility Staff": (
        "En el sótano del edificio de Química (Building C), hay una fuga fuerte de gas amoníaco y cloro. "
        "No tenemos respiradores con filtro adecuado, solo mascarillas de papel. María empezó a toser fuerte "
        "y tuvo mareos graves. El supervisor dijo que no podemos llamar a bomberos porque arruinaría las clases. "
        "El extractor de aire lleva 3 semanas roto."
    ),
}

PRESET_SAFETY_OVERTIME = {
    "title": "Unpaid Overtime & Fatigue",
    "icon": "🟡",
    "description": "Excessive continuous hours, fatigue symptoms, and wage deductions.",
    "Construction Sites": (
        "Worked from 5:30 AM until 9:30 PM straight (16 hours) pouring concrete in 102°F sun. "
        "Only one 15-minute break was allowed. My legs are cramping, dizzy spell almost made me faint into the pit. "
        "Contractor gave only $120 cash, saying 'overtime is not in our budget'. "
        "Half the crew wants to quit tomorrow because we are treated like machines."
    ),
    "College Support & Facility Staff": (
        "Forced to work back-to-back shifts during Homecoming Weekend. Did Friday night dorm cleanout "
        "from 10 PM to 6 AM, then told by management I had to stay until 2 PM for football stadium cleanup (16 hours). "
        "I was so exhausted I couldn't see straight driving the floor scrubber. "
        "Payroll clerk says event hours are considered 'volunteer' and won't be paid overtime. I am ready to quit."
    ),
}

# =====================================================================
# WORKER PORTAL: SHIFT & PAYSLIP SCANNER PRESETS
# =====================================================================

PRESET_TIMESHEET_CONSTRUCTION = (
    "WORKER: Heavy Laborer / Scaffolder\n"
    "DATES: October 24, 2026\n"
    "CLOCK-IN: 06:00 AM\n"
    "CLOCK-OUT: 08:30 PM\n"
    "TOTAL TIME: 14.5 Hours continuous (one 20m lunch)\n"
    "AGREED HOURLY RATE: $18.00 / hour\n"
    "OVERTIME CLAUSE: Standard 1.5x after 8 hours ($27.00/hr)\n"
    "PAYMENT RECEIVED: $160.00 cash envelope from site foreman\n"
    "NOTES: Deducted $20 for site drinking water and transportation. Refused overtime pay."
)

PRESET_TIMESHEET_COLLEGE = (
    "EMPLOYEE: Night Custodial Staff - Hall of Arts & Student Union\n"
    "PAY PERIOD: Weekend Campus Commencement Prep (Oct 25)\n"
    "HOURS LOGGED: Friday 4:00 PM to Saturday 6:00 AM (14.0 Hours total)\n"
    "REGULAR HOURLY WAGE: $16.50 / hr\n"
    "EXPECTED OVERTIME RATE: $24.75 / hr (for 6 overtime hours)\n"
    "STIPEND / PAYSLIP RECORDED: $132.00 (Standard 8 hours paid, 6 hours uncredited)\n"
    "ANOMALIES: Supervisor marked overtime as campus volunteer event. Denied meal voucher."
)

PRESET_TIMESHEET_COMPLIANT = (
    "WORKER: Campus Grounds Maintenance Specialist\n"
    "DATE: October 26, 2026\n"
    "HOURS: 07:30 AM to 04:00 PM (8.0 billable hours + 30 min meal break)\n"
    "HOURLY RATE: $20.00 / hour\n"
    "COMPENSATION PAID: $160.00 direct deposit\n"
    "STATUS: Fully compliant with OSHA rest intervals and state wage laws."
)

# =====================================================================
# ADMIN DASHBOARD: AGGREGATED SEED RECORDS
# =====================================================================

def get_initial_safety_reports() -> List[Dict[str, Any]]:
    """Return pre-populated high-fidelity reports for immediate Admin Dashboard demonstration."""
    return [
        {
            "id": "FS-SEC-101",
            "timestamp": "2026-10-27 08:15",
            "sector": "Construction Sites",
            "detected_language": "Hindi / English Mix",
            "translated_summary": "Scaffolding plank fractured on the 4th floor; worker nearly fell 35 feet. Supervisor denied safety harnesses to accelerate pouring schedule. Exposed 440V cables dangling near wet concrete.",
            "anonymized_report": "Worker reported that on the fourth floor, a wooden scaffolding plank snapped, almost causing a colleague to fall 35 feet. The site supervisor allegedly pressured the crew to speed up without fall protection harnesses. Exposed 440V high-voltage electrical wires are submerged near wet concrete puddles.",
            "urgency_level": "urgent",
            "red_flags": [
                "Fractured scaffolding plank at 35ft elevation",
                "Lack of mandatory fall arrest harnesses",
                "Exposed 440V dangling electrical wiring near water/puddles",
                "Management coercion ignoring safety stop-work rights",
            ],
            "fatigue_warning": True,
            "confidence": "high",
            "attrition_risk": "high",
            "status": "Escalated to OSHA Inspector",
            "actionable_recommendations": [
                "Issue immediate stop-work order for Sector 4 scaffolding",
                "Conduct mandatory fall-protection harness inspection",
                "Depower and re-insulate 440V wiring",
            ],
        },
        {
            "id": "FS-SEC-102",
            "timestamp": "2026-10-27 07:45",
            "sector": "College Support & Facility Staff",
            "detected_language": "Spanish",
            "translated_summary": "Strong ammonia and chlorine chemical fumes detected in Building C basement. Custodial crew lacked particulate respirators; worker suffered acute respiratory distress. Exhaust ventilation non-functional.",
            "anonymized_report": "Custodial staff in the science facility basement reported severe ammonia and chlorine vapor accumulation. Personnel were issued only disposable dust masks instead of organic vapor respirators. One team member experienced severe coughing and dizziness. Ventilation ducting has been inoperable for three weeks.",
            "urgency_level": "urgent",
            "red_flags": [
                "Toxic chemical fumes (chlorine/ammonia) in confined basement",
                "Substandard PPE (dust masks instead of chemical respirators)",
                "Worker acute respiratory distress and coughing",
                "Broken exhaust ventilation fan unaddressed for 3 weeks",
            ],
            "fatigue_warning": False,
            "confidence": "high",
            "attrition_risk": "high",
            "status": "Hazard Team Dispatched",
            "actionable_recommendations": [
                "Evacuate Building C sub-level immediately",
                "Supply NIOSH-approved dual-cartridge respirators",
                "Emergency maintenance on basement air exhaust system",
            ],
        },
        {
            "id": "FS-SEC-103",
            "timestamp": "2026-10-26 21:30",
            "sector": "Construction Sites",
            "detected_language": "English",
            "translated_summary": "16-hour continuous concrete pour shift under high heat (102°F). Worker suffered heat exhaustion cramps. Cash payment shorted overtime compensation.",
            "anonymized_report": "A laborer reported an excessive 16-hour shift under high ambient temperatures. The worker experienced severe muscle cramps and fainting spells due to inadequate water replenishment. Cash compensation of $120 was paid, omitting legally required overtime rates.",
            "urgency_level": "see_soon",
            "red_flags": [
                "16-hour excessive shift without mandatory rest intervals",
                "Heat illness risk in 102°F temperatures",
                "Unpaid overtime wage violation",
            ],
            "fatigue_warning": True,
            "confidence": "high",
            "attrition_risk": "high",
            "status": "Pending Payroll Review",
            "actionable_recommendations": [
                "Enforce OSHA maximum 10-hour daily shift cap",
                "Establish shaded cooling stations with electrolyte provisions",
                "Audit payroll for statutory overtime wage restitution",
            ],
        },
        {
            "id": "FS-SEC-104",
            "timestamp": "2026-10-26 18:20",
            "sector": "College Support & Facility Staff",
            "detected_language": "English",
            "translated_summary": "Elevator in central library broken for 10 days; custodial staff forced to haul 60lb chemical barrels and waste bags up 4 flights of stairs.",
            "anonymized_report": "Facility staff reported that the service elevator in the main library has been down for 10 days. Cleaners are carrying heavy 60-pound barrels and trash sacks up and down flights of stairs, leading to multiple lower back strain complaints.",
            "urgency_level": "see_soon",
            "red_flags": [
                "Ergonomic injury hazard from manual heavy lifting (60lb barrels)",
                "Prolonged infrastructure failure impacting worker safety",
            ],
            "fatigue_warning": True,
            "confidence": "high",
            "attrition_risk": "medium",
            "status": "Work Order Assigned",
            "actionable_recommendations": [
                "Prioritize commercial elevator technician repair",
                "Provide stair-climbing hand trucks or restrict container sizes to 25lbs",
            ],
        },
        {
            "id": "FS-SEC-105",
            "timestamp": "2026-10-26 14:10",
            "sector": "College Support & Facility Staff",
            "detected_language": "English",
            "translated_summary": "Routine evening maintenance in Dormitory West completed. All trash rooms sanitized, safety gear stocked, no violations observed.",
            "anonymized_report": "Staff reported successful routine cleaning of Dormitory West. Fire exits verified clear of clutter, and chemical supply cabinets safely locked. Restock of personal protective gloves requested for next week.",
            "urgency_level": "routine",
            "red_flags": [],
            "fatigue_warning": False,
            "confidence": "high",
            "attrition_risk": "low",
            "status": "Resolved / Logged",
            "actionable_recommendations": [
                "Fulfill routine order for size L nitrile gloves",
            ],
        },
    ]


def get_initial_shift_records() -> List[Dict[str, Any]]:
    """Return pre-populated timesheet audit records for the Admin Dashboard."""
    return [
        {
            "id": "TS-091",
            "worker_role": "Scaffolder & Concrete Pourer",
            "sector": "Construction Sites",
            "shift_date_or_period": "2026-10-25",
            "total_hours_worked": 14.5,
            "standard_hours": 8.0,
            "overtime_hours": 6.5,
            "base_hourly_rate": 18.0,
            "overtime_hourly_rate": 27.0,
            "expected_standard_pay": 144.0,
            "expected_overtime_pay": 175.5,
            "total_expected_fair_pay": 319.5,
            "reported_pay": 160.0,
            "wage_shortfall": 159.5,
            "fatigue_alert": True,
            "fatigue_level": "critical",
            "fatigue_reason": "14.5 continuous hours worked. Extreme fatigue hazard exceeding safe physical thresholds.",
            "anomalies": ["Refused 6.5 hours overtime compensation", "Illegal $20 deduction for water"],
        },
        {
            "id": "TS-092",
            "worker_role": "Campus Event Night Custodian",
            "sector": "College Support & Facility Staff",
            "shift_date_or_period": "2026-10-24",
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
            "fatigue_reason": "14-hour double shift without sleep. Serious cognitive fatigue and vehicle operating risk.",
            "anomalies": ["Unpaid 6 overtime hours misclassified as volunteer work"],
        },
        {
            "id": "TS-093",
            "worker_role": "Carpentry Apprentice",
            "sector": "Construction Sites",
            "shift_date_or_period": "2026-10-24",
            "total_hours_worked": 10.0,
            "standard_hours": 8.0,
            "overtime_hours": 2.0,
            "base_hourly_rate": 20.0,
            "overtime_hourly_rate": 30.0,
            "expected_standard_pay": 160.0,
            "expected_overtime_pay": 60.0,
            "total_expected_fair_pay": 220.0,
            "reported_pay": 180.0,
            "wage_shortfall": 40.0,
            "fatigue_alert": True,
            "fatigue_level": "warning",
            "fatigue_reason": "10-hour shift exceeds daily 8h baseline; moderate physical fatigue.",
            "anomalies": ["Overtime paid at standard 1.0x rate instead of mandatory 1.5x"],
        },
        {
            "id": "TS-094",
            "worker_role": "Dining Hall Utility Staff",
            "sector": "College Support & Facility Staff",
            "shift_date_or_period": "2026-10-26",
            "total_hours_worked": 8.0,
            "standard_hours": 8.0,
            "overtime_hours": 0.0,
            "base_hourly_rate": 17.0,
            "overtime_hourly_rate": 25.5,
            "expected_standard_pay": 136.0,
            "expected_overtime_pay": 0.0,
            "total_expected_fair_pay": 136.0,
            "reported_pay": 136.0,
            "wage_shortfall": 0.0,
            "fatigue_alert": False,
            "fatigue_level": "normal",
            "fatigue_reason": "Compliant 8-hour shift.",
            "anomalies": [],
        },
    ]
