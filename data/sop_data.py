"""Structured content definitions and evaluation questions for the 12 hospital SOP documents.

This module defines comprehensive, multi-page standard operating procedures (SOPs)
for Metropolitan Health System, containing realistic clinical workflows, concrete numbers,
durations, thresholds, responsible roles, and deliberate thematic overlaps (gloves,
documentation, escalation).

Strict Privacy Compliance:
All policies, personnel titles, procedures, and data points are entirely synthetic.
"""

from __future__ import annotations

from typing import Any, Dict, List

SOP_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "infection_control": {
        "filename": "sop_infection_control.pdf",
        "doc_id": "SOP-INF-2026-01",
        "department": "Infection Prevention & Hospital Epidemiology",
        "subtitle": "METROPOLITAN HEALTH SYSTEM — CLINICAL POLICY & PROCEDURE",
        "title": "STANDARD OPERATING PROCEDURE: INFECTION PREVENTION AND TRANSMISSION-BASED ISOLATION CONTROLS",
        "effective_date": "2026-01-01",
        "review_cycle": "Annual",
        "pages": [
            # Page 1
            [
                {
                    "type": "section",
                    "heading": "1.0 Purpose and Operational Objective",
                    "content": [
                        "This standard operating procedure defines clinical guidelines and operational requirements for preventing healthcare-associated infections (HAIs) across inpatient wards, surgical suites, and intensive care units. The primary objective is early pathogen identification, effective barrier precautions, and safe decontamination workflows to minimize cross-transmission risk.",
                        "Preventing nosocomial transmission requires disciplined adherence to standard and transmission-based precautions. All healthcare personnel must maintain active vigilance regarding microbiological transmission routes, personal protective equipment integrity, and clean-to-dirty workflow transitions.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "2.0 Scope and Regulatory Authority",
                    "content": [
                        "This policy applies to all clinical personnel, nursing staff, allied healthcare providers, environmental services teams, and visiting observers. Compliance with CDC guidelines, WHO recommendations, and state department of health infection benchmarks is mandatory. Failure to adhere to isolation protocols triggers immediate clinical review.",
                        "Unit charge nurses and department medical directors bear direct administrative accountability for monitoring staff adherence within their clinical areas. The Hospital Epidemiologist retains ultimate executive authority to institute emergency quarantine or ward restrictions.",
                    ],
                },
            ],
            # Page 2
            [
                {
                    "type": "section",
                    "heading": "3.0 Standard Universal Precautions & Hand Hygiene",
                    "content": [
                        "Standard universal precautions must be practiced for every patient contact regardless of diagnosis. Hand hygiene must be executed according to the WHO 5 Moments protocol. Healthcare workers must sanitize hands with alcohol-based rub (minimum 3 mL for 20 seconds) or wash with soap and running water for at least 40 seconds when hands are visibly soiled.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "4.0 Personal Protective Equipment: Gloves, Gowns, and Respirators",
                    "content": [
                        "Clinical personnel must don nitrile examination gloves meeting ASTM D6319 standards prior to contacting blood, bodily fluids, non-intact skin, or contaminated mucous membranes. Gloves must be changed between separate procedures on the same patient and immediately upon exiting the room. Double-gloving is prohibited during routine care and restricted to orthopedic surgery and gross biohazard containment. Disposable fluid-resistant isolation gowns (AAMI Level 3) and NIOSH-certified N95 respirators must be donned prior to entering designated isolation suites.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [85, 105, 105, 105, 100],
                    "header": ["Care Encounter", "Gloves Specification", "Isolation Gown", "Respiratory Protection", "Eye Protection"],
                    "rows": [
                        ["Routine Ward Check", "ASTM D6319 Nitrile", "None required", "Standard Surgical Mask", "None (unless splash)"],
                        ["Wound Irrigation", "ASTM D6319 Nitrile", "AAMI Level 3 Fluid-Resist", "Surgical Mask with Shield", "Full Face Shield"],
                        ["Contact Isolation", "ASTM D6319 Nitrile", "AAMI Level 2 Impervious", "Standard Surgical Mask", "Optional"],
                        ["Airborne Isolation", "ASTM D6319 Nitrile", "AAMI Level 3 Fluid-Resist", "Fit-Tested N95 / PAPR", "Protective Goggles"],
                        ["Bronchoscopy Suite", "Sterile Surgical Nitrile", "AAMI Level 4 Barrier Gown", "Fit-Tested N95 / PAPR", "Full Face Shield"],
                    ],
                },
            ],
            # Page 3
            [
                {
                    "type": "section",
                    "heading": "5.0 Transmission-Based Isolation Categories",
                    "content": [
                        "Patients presenting with suspected or confirmed epidemiologically significant pathogens require immediate placement into transmission-based isolation. Clinical staff must adhere to category-specific precautions including Contact, Droplet, Airborne, and Protective isolation.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "6.0 Airborne Infection Isolation Room (AIIR) Specifications",
                    "content": [
                        "Patients placed under Airborne Precautions (e.g., active pulmonary tuberculosis, measles, disseminated varicella-zoster) must be housed exclusively in an Airborne Infection Isolation Room (AIIR). The AIIR must maintain negative pressure relative to surrounding hallways of at least -2.5 Pa (-0.01 inches of water column) and achieve ≥12 air changes per hour (ACH) for existing facilities and ≥14 ACH for newly constructed rooms. Exhaust air must be vented directly outside or filtered through a certified HEPA filter (≥99.97% efficiency for 0.3 micron particles). Negative pressure indicators must be visually inspected and logged by facilities staff every 24 hours.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [70, 110, 110, 110, 100],
                    "header": ["Isolation Tier", "Clinical Indicators", "Required PPE", "Ventilation Control", "Decontamination"],
                    "rows": [
                        ["Contact", "MRSA, VRE, C. diff, scabies", "Gown and gloves upon entry", "Standard positive/neutral", "Sporicidal bleach if C. diff"],
                        ["Droplet", "Influenza, pertussis, mumps", "Surgical mask within 6 feet", "Standard positive/neutral", "Quat ammonium wipe down"],
                        ["Airborne", "TB, measles, chickenpox", "N95 respirator or PAPR", "AIIR (≥12 ACH, -2.5 Pa)", "UV-C post-discharge + air clear"],
                        ["Protective", "Neutropenic (<500 ANC), HSCT", "Mask, gown, strict barrier", "Positive pressure (HEPA)", "Daily sporicidal wiping"],
                    ],
                },
            ],
            # Page 4
            [
                {
                    "type": "section",
                    "heading": "7.0 Environmental Decontamination & Disinfection Timelines",
                    "content": [
                        "Routine environmental cleaning must occur at least twice daily for high-touch surfaces (bed rails, IV poles, call buttons, telemetry monitors). Disinfectant contact times are strictly enforced: quaternary ammonium compound wipes require a minimum wet dwell time of 4 minutes, while 0.5% sodium hypochlorite (1:10 bleach dilution, ~5,000 ppm available chlorine) requires a minimum contact wet time of 10 minutes for bleach. Wiping dry before the dwell time has elapsed invalidates disinfection and necessitates a full re-wipe.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "8.0 Terminal Cleaning Workflow post-Discharge",
                    "content": [
                        "Terminal cleaning of an isolation room following patient discharge requires complete stripping of bed linens into water-soluble laundry bags, followed by a top-to-bottom wipe-down of all fixtures. For Clostridioides difficile or Candida auris rooms, sporicidal bleach solution or vaporized hydrogen peroxide (VHP) is mandatory. After terminal wipe-down, the room must remain vacant for at least 45 minutes to allow complete atmospheric air clearance.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [110, 120, 110, 160],
                    "header": ["Disinfectant Chemical", "Target Microorganisms", "Wet Contact Time", "Clinical Application"],
                    "rows": [
                        ["Quaternary Ammonium", "Enveloped viruses, bacteria", "4 minutes wet contact", "General non-isolation beds, desks"],
                        ["Sodium Hypochlorite (Bleach)", "C. difficile spores, Norovirus", "10 minutes for bleach", "Enteric isolation, terminal rooms"],
                        ["Hydrogen Peroxide (VHP)", "Fungal spores, C. auris", "60 minutes dwell cycle", "Specialized terminal room fogging"],
                        ["70% Isopropyl Alcohol", "Blood glucose monitors, probes", "1 minute wet contact", "Small point-of-care medical devices"],
                    ],
                },
            ],
            # Page 5
            [
                {
                    "type": "section",
                    "heading": "9.0 Medical Device Reprocessing & Sterilization",
                    "content": [
                        "Non-critical items (blood pressure cuffs, pulse oximeter probes, stethoscopes) must be decontaminated between patients using intermediate-level disinfectant wipes. Semi-critical items (endoscopes, transesophageal probes) require high-level disinfection with 2.4% glutaraldehyde or orthophthalaldehyde (OPA) with automated cycle validation. Critical surgical instruments require terminal steam autoclave sterilization at 132°C (270°F) for 4 minutes at 30 psi.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "10.0 Outbreak Surveillance & Microbiological Alert System",
                    "content": [
                        "The hospital infection control software interface monitors laboratory information system (LIS) feeds in real time. Automated electronic alerts are generated for multidrug-resistant organisms (MDRO), including methicillin-resistant Staphylococcus aureus (MRSA), vancomycin-resistant Enterococcus (VRE), and carbapenem-resistant Enterobacteriaceae (CRE). The Infection Preventionist on call must review microbiological alerts within 60 minutes of issuance.",
                    ],
                },
            ],
            # Page 6
            [
                {
                    "type": "section",
                    "heading": "11.0 EMR Documentation and Quarantine Tagging",
                    "content": [
                        "The admitting nurse or attending physician must document the assigned isolation tier in the EMR within 2 hours of microbiology alert or clinical suspicion. The electronic chart must display an active isolation banner across all clinical modules. A physical color-coded isolation sign (Contact = Yellow, Droplet = Orange, Airborne = Blue) must be posted outside the patient door within 15 minutes of order entry.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "12.0 Clinical Governance, Audit, and Breach Escalation",
                    "content": [
                        "The Infection Control Committee conducts weekly unannounced observational audits across all units. Hand hygiene compliance targets are set at ≥95%. Any cluster of two or more nosocomial infections in the same unit within a 14-day window requires an immediate sentinel outbreak investigation and notification of the Chief Medical Officer within 4 hours. An isolation breach resulting in exposed staff or unshielded patients requires an incident ticket within 2 hours.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 105, 115, 165],
                    "header": ["Surveillance Metric", "Target Threshold", "Audit Cadence", "Escalation Authority"],
                    "rows": [
                        ["Hand Hygiene Compliance", "≥ 95% compliance", "Weekly unannounced", "Unit Charge Nurse & CNO"],
                        ["AIIR Negative Pressure", "-2.5 Pa differential", "Every 24 hours", "Facilities Operations Manager"],
                        ["Nosocomial Cluster (≥ 2)", "0 tolerance cluster", "Real-time monitoring", "Chief Medical Officer within 4 hours"],
                        ["Terminal Room Bioluminescence", "< 250 Relative Light Units", "Monthly random 20%", "Environmental Services Director"],
                    ],
                },
            ],
            # Page 7
            [
                {
                    "type": "section",
                    "heading": "13.0 Staff Health, Immunization, and Bloodborne Pathogen Post-Exposure",
                    "content": [
                        "All clinical employees must maintain current occupational immunizations (Hepatitis B, MMR, Varicella, Tdap, annual Influenza). Following any sharps injury or mucosal splash with potentially infectious blood or body fluid, the staff member must immediately flush the site with soap and water or sterile saline for 15 minutes. The employee must report to Occupational Health or the Emergency Department for post-exposure prophylaxis evaluation within 2 hours.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "14.0 Document Revision History and Committee Approvals",
                    "content": [
                        "This SOP is reviewed annually and updated promptly upon any CDC or state regulatory modification. Revisions must be approved by the Infection Control Committee Chair and Hospital Chief Medical Officer.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [70, 85, 195, 150],
                    "header": ["Version", "Effective Date", "Summary of Revisions", "Approved Authority"],
                    "rows": [
                        ["v1.0", "2024-01-01", "Initial institutional policy release", "Infection Control Committee"],
                        ["v2.0", "2025-01-01", "Updated sporicidal dwell times and AIIR metrics", "Epidemiology Governance Panel"],
                        ["v3.0", "2026-01-01", "Aligned ASTM glove specifications and CRE alerts", "Chief Medical Officer"],
                    ],
                },
            ],
        ],
    },
    "discharge_process": {
        "filename": "sop_discharge_process.pdf",
        "doc_id": "SOP-DIS-2026-02",
        "department": "Care Coordination & Inpatient Medicine",
        "subtitle": "METROPOLITAN HEALTH SYSTEM — CLINICAL POLICY & PROCEDURE",
        "title": "STANDARD OPERATING PROCEDURE: INPATIENT DISCHARGE PROCESS AND CARE TRANSITIONS",
        "effective_date": "2026-01-01",
        "review_cycle": "Annual",
        "pages": [
            # Page 1
            [
                {
                    "type": "section",
                    "heading": "1.0 Objective and Target Departure Timelines",
                    "content": [
                        "Safe, timely discharge planning begins on admission. The goal of this protocol is to reduce preventable 30-day hospital readmissions, eliminate post-discharge adverse drug events, and ensure smooth coordination between hospital teams, post-acute facilities, and primary care physicians. The institutional daily target hospital departure cutoff is 11:00 AM.",
                        "Optimizing inpatient throughput directly supports emergency department boarding reduction and operating room capacity. Early morning discharge initiatives require proactive multi-disciplinary preparation starting 24 hours prior to anticipated departure.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "2.0 Care Coordination and Interdisciplinary Daily Rounds",
                    "content": [
                        "Case managers and unit care coordinators must lead daily interdisciplinary discharge huddles at 08:30 AM. Each patient's estimated date of discharge (EDD) must be confirmed or adjusted within the EMR. Barrier identification (transportation, financial assistance, skilled nursing facility placement, durable medical equipment) must occur within 24 hours of inpatient admission.",
                    ],
                },
            ],
            # Page 2
            [
                {
                    "type": "section",
                    "heading": "3.0 Attending Physician Clinical Sign-Off Requirements",
                    "content": [
                        "The attending physician must complete and digitally sign the formal discharge summary within 24 hours of patient departure. For patients transferring to skilled nursing facilities (SNF) or acute rehab, the preliminary discharge order, medication list, and transfer packet must be finalized prior to physical departure from the unit.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "4.0 Three-Way Medication Reconciliation Protocol",
                    "content": [
                        "A clinical pharmacist or dedicated discharge nurse must perform three-way medication reconciliation: comparing pre-admission medications, active inpatient medications, and intended outpatient prescriptions. Every prescribed medication must have an explicitly documented indication, dosage, dosage unit, administration frequency, and intended treatment duration. Verbal instructions alone are prohibited.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [110, 110, 130, 150],
                    "header": ["Reconciliation Phase", "Responsible Role", "Core Clinical Deliverable", "Quality Check Benchmark"],
                    "rows": [
                        ["Admission History", "Triage Pharmacist", "Verified home medication list", "Completed within 12 hours"],
                        ["Transfer / Stepdown", "Staff Nurse / Resident", "Active inpatient drug review", "Prior to inter-unit transfer"],
                        ["Discharge Reconciliation", "Clinical Pharmacist", "Outpatient electronic prescriptions", "Signed prior to patient departure"],
                        ["Bedside Meds-to-Beds", "Outpatient Pharmacy", "Physical delivery of 30-day supply", "Delivered by 09:30 AM discharge day"],
                    ],
                },
            ],
            # Page 3
            [
                {
                    "type": "section",
                    "heading": "5.0 Phased Morning Milestones and Timetable",
                    "content": [
                        "To achieve the target hospital departure cutoff of 11:00 AM, clinical teams must adhere to phased milestones: Pre-Discharge T-24h (identify anticipated discharge by 16:00), Morning Review T-4h (07:30 confirm DME and insurance), Medication Finalization (09:00 Meds-to-Beds delivery), Patient Education (10:00 teach-back), and Departure (11:00 wheelchair escort).",
                    ],
                },
                {
                    "type": "section",
                    "heading": "6.0 Patient and Family Teach-Back Education",
                    "content": [
                        "The primary bedside nurse must conduct a comprehensive 20-minute teach-back education session with the patient and designated caregiver. Education must cover newly prescribed medications, surgical wound care, physical activity restrictions, dietary modifications, and emergency warning signs ('Red Flags'). The patient must verbalize understanding without prompting.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [90, 80, 110, 220],
                    "header": ["Workflow Stage", "Target Milestone", "Lead Role", "Mandatory Deliverables"],
                    "rows": [
                        ["Pre-Discharge T-24h", "Day prior by 16:00", "Attending / Resident", "Identify anticipated discharge; draft medication list; verify ride home"],
                        ["Morning Review T-4h", "Day of discharge 07:30", "Care Coordinator", "Confirm DME delivery; finalize insurance approval; verify rehab bed"],
                        ["Medication Finalization", "Day of discharge 09:00", "Clinical Pharmacist", "Resolve drug discrepancies; complete bedside Meds-to-Beds delivery"],
                        ["Patient Education", "Day of discharge 10:00", "Primary Nurse", "Teach-back technique for Red Flag symptoms; review follow-up schedule"],
                        ["Departure & Transport", "Day of discharge 11:00", "Unit Charge Nurse", "Wheelchair escort to exit; update bed tracking system to dirty/cleaning"],
                    ],
                },
            ],
            # Page 4
            [
                {
                    "type": "section",
                    "heading": "7.0 Post-Acute Facility Transfer Protocols (SNF / Rehab)",
                    "content": [
                        "Transfer to post-acute care (SNF, sub-acute rehabilitation, long-term acute care hospital, or hospice) requires a standardized clinical handoff. The care coordinator must transmit the complete electronic transfer packet at least 2 hours before transport arrives. The packet must contain recent laboratory results, last dose of controlled substances given, code status orders (POLST/MOLST), and primary contact details.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "8.0 Durable Medical Equipment (DME) Coordination",
                    "content": [
                        "Durable medical equipment orders (home oxygen concentrators, hospital beds, walkers, wheelchairs, negative pressure wound therapy) must be submitted to approved vendors at least 24 hours prior to planned discharge. Oxygen delivery verification must occur 4 hours prior to departure, confirming flow rate (liters per minute) and delivery modality.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 120, 115, 150],
                    "header": ["Equipment Category", "Payer Authorization Cutoff", "Vendor Delivery Window", "Nursing Verification Step"],
                    "rows": [
                        ["Home Oxygen Concentrator", "24 hours pre-discharge", "Delivered to room by 08:00", "Demonstrate cannula & tank switch"],
                        ["Hospital Bed / Low Air Loss", "48 hours pre-discharge", "Installed at home prior to arrival", "Family confirms home installation"],
                        ["Mobility (Walker/Wheelchair)", "12 hours pre-discharge", "Delivered to bedside by 09:00", "Physical therapist gait training check"],
                        ["Wound Vacuum Therapy", "24 hours pre-discharge", "Vendor setup by 08:30", "Dressing seal tested under suction"],
                    ],
                },
            ],
            # Page 5
            [
                {
                    "type": "section",
                    "heading": "9.0 Infection Control and PPE Protocols During Discharge Transit",
                    "content": [
                        "When discharging or transferring patients from transmission-based isolation, the patient must wear a clean surgical mask during transit through public hallways. Transport personnel must not wear clinical gloves in hospital corridors or passenger elevators; patient escort staff must remove clinical exam gloves and sanitize hands prior to entering public transit discharge lounge. Wheelchairs and stretchers used for transport must undergo intermediate-level surface wipe-down immediately following patient drop-off.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "10.0 Post-Discharge Telephonic Follow-Up (LACE Criteria)",
                    "content": [
                        "High-risk patients (LACE score ≥ 10 or multi-morbid conditions) must receive a telephone follow-up call from the care transition team within 48 to 72 hours post-discharge. The call must assess: (1) medication understanding and pharmacy pickup, (2) red flag warning signs (chest pain, worsening dyspnea, fever > 101°F), (3) scheduled outpatient follow-up appointments, and (4) social support stability. Any acute deterioration triggers immediate primary care provider or triage notification.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [90, 125, 105, 180],
                    "header": ["LACE Factor", "Clinical Measurement", "Points Assigned", "Clinical Interpretation"],
                    "rows": [
                        ["Length of Stay (L)", "< 1 day to ≥ 14 days", "0 to 7 points", "Prolonged acute illness burden"],
                        ["Acuity of Admission (A)", "Elective vs Acute Emergency", "0 or 3 points", "Unplanned acute physiological crisis"],
                        ["Comorbidity (C)", "Charlson Comorbidity Index", "0 to 5 points", "Underlying chronic disease severity"],
                        ["ED Visits (E)", "Visits in prior 6 months", "0 to 4 points", "Frequent acute healthcare utilization"],
                    ],
                },
            ],
            # Page 6
            [
                {
                    "type": "section",
                    "heading": "11.0 Transportation and Bed De-escalation Workflow",
                    "content": [
                        "Once the patient vacates the room, the unit coordinator must update the electronic bed tracking system from 'Occupied' to 'Dirty/Pending Cleaning' within 10 minutes. If the patient does not have reliable private transportation, non-emergent medical transport (NEMT) or hospital taxi vouchers must be confirmed by the case manager before 09:30 AM on the day of discharge.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "12.0 Quality Metrics, Readmission Audit, and Delay Escalation",
                    "content": [
                        "The Hospital Quality Committee tracks 30-day all-cause readmission rates and early discharge compliance monthly. When an inpatient departure is delayed more than 180 minutes past the scheduled release time, the charge nurse must log a delay incident in the bed management portal, and the case escalates to the Inpatient Bed Management Director.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 105, 115, 165],
                    "header": ["Operational KPI", "Institutional Target", "Measurement Interval", "Accountable Lead"],
                    "rows": [
                        ["Discharge by 11:00 AM", "≥ 45% of total discharges", "Weekly unit dashboard", "Nurse Manager & Hospitalist Chief"],
                        ["Discharge by 14:00 PM", "≥ 85% of total discharges", "Monthly department roll-up", "Director of Care Coordination"],
                        ["Medication Rec Concordance", "100% completed prior departure", "Real-time eMAR audit", "Pharmacy Clinical Director"],
                        ["30-Day All-Cause Readmission", "< 11.5% risk-adjusted", "Monthly Quality Committee", "Chief Medical Officer"],
                    ],
                },
            ],
            # Page 7
            [
                {
                    "type": "section",
                    "heading": "13.0 Discharge Against Medical Advice (AMA) Protocol",
                    "content": [
                        "When a competent patient insists on leaving against medical advice, the attending physician or senior resident must conduct an in-person risk discussion explaining potential morbidity or mortality. The clinician must offer alternative outpatient therapies, provide necessary prescriptions, and document the AMA discussion in the EMR within 60 minutes. The AMA form must be witnessed by two healthcare workers.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "14.0 Document Revision and Approval Metadata",
                    "content": [
                        "This SOP is maintained by the Care Coordination and Inpatient Medicine Governance Panel. Biennial review is required.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [70, 85, 195, 150],
                    "header": ["Version", "Effective Date", "Summary of Revisions", "Approved Authority"],
                    "rows": [
                        ["v1.0", "2024-01-01", "Initial discharge transition framework", "Inpatient Operations Committee"],
                        ["v2.0", "2025-01-01", "Added LACE telephonic outreach protocol", "Care Coordination Council"],
                        ["v3.0", "2026-01-01", "Enforced Meds-to-Beds delivery timelines", "Chief Operating Officer"],
                    ],
                },
            ],
        ],
    },
    "billing_financial": {
        "filename": "sop_billing_financial.pdf",
        "doc_id": "SOP-BIL-2026-03",
        "department": "Revenue Cycle & Patient Financial Services",
        "subtitle": "METROPOLITAN HEALTH SYSTEM — ADMINISTRATIVE POLICY & PROCEDURE",
        "title": "STANDARD OPERATING PROCEDURE: HOSPITAL BILLING COMPLIANCE AND CHARGE CAPTURE",
        "effective_date": "2026-01-01",
        "review_cycle": "Annual",
        "pages": [
            # Page 1
            [
                {
                    "type": "section",
                    "heading": "1.0 Purpose and Revenue Cycle Integrity",
                    "content": [
                        "This standard operating procedure governs clinical documentation improvement, point-of-care charge capture, coding integrity, and billing compliance across all inpatient and outpatient divisions. The hospital clean claim rate target is ≥ 96% on first-pass insurer submissions.",
                        "A compliant revenue cycle balances accurate reimbursement with transparent patient billing practices. Ethical billing mandates that every charge reflects verifiable documentation in the medical record without duplicate entry or unbundled service codes.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "2.0 Regulatory Framework (CMS, HIPAA, False Claims Act)",
                    "content": [
                        "All billing activities must strictly adhere to CMS guidelines, HIPAA privacy regulations, and the False Claims Act. Billing for services not documented in the medical record is strictly prohibited. Every claim must reflect medically necessary care substantiated by contemporaneous clinical entries.",
                    ],
                },
            ],
            # Page 2
            [
                {
                    "type": "section",
                    "heading": "3.0 Point-of-Care Charge Capture & Timelines",
                    "content": [
                        "Clinical departments must enter all charges within 24 hours of service delivery or patient discharge. High-volume procedural units (surgical suites, cardiac catheterization labs, endoscopy) must complete electronic supply and implant reconciliation prior to patient transfer to recovery. Unentered charges older than 72 hours are flagged as late charges and require departmental chair sign-off.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "4.0 Coding Validation and DRG Optimization",
                    "content": [
                        "Certified professional coders review clinical documentation to assign ICD-10-CM diagnosis codes, ICD-10-PCS procedural codes, and CPT/HCPCS codes. Queries to attending physicians regarding ambiguous or conflicting diagnoses must be issued through the EMR clinical documentation query portal and answered within 48 hours.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Clinical Service Area", "Charge Capture Cutoff", "Reconciliation Cadence", "Departmental Lead"],
                    "rows": [
                        ["Operating Room & Cath Lab", "Within 4 hours of case end", "Daily implant reconciliation", "Surgical Services Business Mgr"],
                        ["Inpatient Acute Nursing", "Within 24 hours of service", "Daily shift change review", "Unit Nurse Manager"],
                        ["Emergency Department", "Within 12 hours of discharge", "Twice daily unbilled scrub", "ED Patient Access Director"],
                        ["Outpatient Specialty Clinics", "By 18:00 on day of service", "Weekly billing ledger audit", "Ambulatory Operations Lead"],
                    ],
                },
            ],
            # Page 3
            [
                {
                    "type": "section",
                    "heading": "5.0 Charge Description Master (CDM) Maintenance",
                    "content": [
                        "The hospital Charge Description Master (CDM) contains all billable items, procedure codes, revenue codes, and standard price benchmarks. The CDM Committee convenes quarterly to update codes according to annual CMS and AMA revisions. Department managers must submit new item charge requests at least 30 days prior to introducing novel clinical supplies.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "6.0 Prior Authorization and Medical Necessity Screening",
                    "content": [
                        "Elective admissions and scheduled high-cost outpatient diagnostic imaging (MRI, PET, CT) require verified insurer prior authorization at least 3 business days prior to the date of service. Unscheduled emergency care is exempt from prior authorization under EMTALA regulations; notification to commercial payers must occur within 24 hours of emergency admission.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [120, 110, 120, 150],
                    "header": ["Procedure Category", "Prior Auth Deadline", "Verification Channel", "Action if Unauthorized"],
                    "rows": [
                        ["Elective Inpatient Surgery", "5 business days prior", "Electronic EDI / Payer Portal", "Case postponed until cleared"],
                        ["Outpatient MRI / CT / PET", "3 business days prior", "Automated pre-cert clearinghouse", "Patient advised of out-of-pocket risk"],
                        ["Specialty Biologic Infusions", "7 business days prior", "Specialty pharmacy coordination", "Treatment rescheduled"],
                        ["Emergency Trauma Admission", "Exempt under EMTALA", "Post-admit notice in 24 hours", "Commercial notification submission"],
                    ],
                },
            ],
            # Page 4
            [
                {
                    "type": "section",
                    "heading": "7.0 Financial Assistance Policy (FAP) and Poverty Guidelines",
                    "content": [
                        "In accordance with Section 501(r) of the Internal Revenue Code, the hospital provides financial relief to eligible low-income patients. Uninsured patients with verified household income ≤ 250% of the Federal Poverty Level (FPL) receive a 100% charity care discount. Patients with income between 251% and 400% of the FPL qualify for a 50% sliding scale discount on out-of-pocket balances.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "8.0 Patient Financial Counseling and Payment Arrangements",
                    "content": [
                        "Financial counselors must meet with uninsured or underinsured patients during inpatient admission or within 30 days post-discharge. Interest-free payment plans are available over 12 to 36 months depending on outstanding liability, with a minimum monthly payment of $25.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [105, 115, 120, 160],
                    "header": ["Income Level (% of FPL)", "Single Person Threshold", "Family of 4 Threshold", "Charity Care Discount Applied"],
                    "rows": [
                        ["≤ 250% FPL", "Up to $37,650 annually", "Up to $78,000 annually", "100% write-off (full charity)"],
                        ["251% to 300% FPL", "$37,651 to $45,180", "$78,001 to $93,600", "75% sliding scale discount"],
                        ["301% to 400% FPL", "$45,181 to $60,240", "$93,601 to $124,800", "50% sliding scale discount"],
                        ["> 400% FPL (Catastrophic)", "Medical debt > 30% income", "Medical debt > 30% income", "Capped at uninsured fee schedule"],
                    ],
                },
            ],
            # Page 5
            [
                {
                    "type": "section",
                    "heading": "9.0 Itemized Statement Generation and Billing Inquiries",
                    "content": [
                        "Patients have the right to request a complete itemized billing statement detailing every billed supply, pharmaceutical, and professional fee. The Patient Financial Services department must generate and dispatch the itemized statement within 3 business days of the request. Statements must clearly explain insurance adjudication and patient responsibility.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "10.0 Dispute Resolution and Charge Grievance Process",
                    "content": [
                        "Patients may dispute any billed charge in writing or via the patient portal within 180 days of statement issuance. Disputed charges exceeding $5,000 must be reviewed by the Patient Accounts Manager and escalated to the Director of Revenue Cycle within 48 hours. Collection activity is frozen during dispute investigation.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 125, 150],
                    "header": ["Dispute Value Range", "Investigating Authority", "Resolution SLA", "Account Collection Status"],
                    "rows": [
                        ["Under $500", "Patient Service Specialist", "5 business days", "Temporary hold on statements"],
                        ["$500 to $5,000", "Revenue Cycle Supervisor", "10 business days", "Formal collection freeze"],
                        ["Over $5,000", "Director of Revenue Cycle", "15 business days (escalate 48h)", "Full legal and statement freeze"],
                        ["Clinical Coding Dispute", "HIM Coding Compliance Lead", "14 business days", "Audit hold pending physician review"],
                    ],
                },
            ],
            # Page 6
            [
                {
                    "type": "section",
                    "heading": "11.0 Revenue Cycle Internal Audit & Physical Inventory Checks",
                    "content": [
                        "Revenue cycle compliance auditors conduct monthly sampling of 50 randomly selected inpatient records. When auditors perform physical barcode inspections in high-value sterile supply depots (implants, pacemakers, stents), billing auditors entering sterile supply depots must wear clean lint-free nitrile gloves when inspecting barcode lot numbers. Audit findings are reported to the Audit and Compliance Committee quarterly.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "12.0 Compliance Escalation and Anti-Fraud Reporting",
                    "content": [
                        "Any employee who identifies potential upcoding, unbundling, double billing, or ghost billing must report the concern to the Hospital Compliance Hotline or directly to the Chief Compliance Officer within 24 hours. The hospital maintains a strict non-retaliation policy under the Federal Whistleblower Protection Act.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Compliance Risk Area", "Sampling Method", "Audit Cadence", "Escalation Threshold"],
                    "rows": [
                        ["Evaluation & Management (E/M)", "30 random charts / provider", "Quarterly", "Discordance rate > 10%"],
                        ["Implant Charge Capture", "100% of cases > $10,000", "Monthly reconciliation", "Unbilled variance > $1,000"],
                        ["Observation vs Inpatient Status", "50 random short-stay charts", "Monthly concurrent review", "Condition Code 44 defects"],
                        ["Suspected Fraud / Abuse", "Direct hotline allegations", "Immediate investigation", "Chief Compliance Officer in 24 hours"],
                    ],
                },
            ],
            # Page 7
            [
                {
                    "type": "section",
                    "heading": "13.0 Bad Debt Write-Off and Extraordinary Collection Actions",
                    "content": [
                        "Accounts with outstanding balances post-adjudication receive four billing notices over a 120-day period. Extraordinary collection actions (credit bureau reporting, legal lawsuits, liens) are strictly prohibited before 120 days from the initial post-discharge statement. Bad debt write-offs exceeding $25,000 require CFO signature.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "14.0 Document Control and Administrative Endorsements",
                    "content": [
                        "This SOP is reviewed annually by the Revenue Cycle Steering Committee and ratified by the Chief Financial Officer.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [70, 85, 195, 150],
                    "header": ["Version", "Effective Date", "Summary of Revisions", "Approved Authority"],
                    "rows": [
                        ["v1.0", "2024-01-01", "Initial revenue cycle policy release", "Finance Governance Committee"],
                        ["v2.0", "2025-01-01", "Revised 501(r) poverty brackets and dispute tiers", "Revenue Cycle Steering Group"],
                        ["v3.0", "2026-01-01", "Standardized supply depot glove auditing protocol", "Chief Financial Officer"],
                    ],
                },
            ],
        ],
    },
    "medication_safety": {
        "filename": "sop_medication_safety.pdf",
        "doc_id": "SOP-MED-2026-04",
        "department": "Pharmacy & Therapeutics Committee",
        "subtitle": "METROPOLITAN HEALTH SYSTEM — CLINICAL PHARMACY POLICY",
        "title": "STANDARD OPERATING PROCEDURE: HIGH-ALERT MEDICATION SAFETY AND INFUSION CONTROLS",
        "effective_date": "2026-01-01",
        "review_cycle": "Annual",
        "pages": [
            # Page 1
            [
                {
                    "type": "section",
                    "heading": "1.0 Safety Mandate & High-Alert Drug Classification",
                    "content": [
                        "High-alert medications bear a heightened risk of causing significant patient harm when used in error. This protocol enforces strict prescribing safeguards, smart infusion pump guardrails, and independent double-checks for all designated high-alert pharmaceuticals (insulin, heparin, narcotics, chemotherapeutic agents, concentrated electrolytes).",
                        "The Pharmacy and Therapeutics (P&T) Committee maintains the institutional high-alert formulary list based on ISMP recommendations. Specific storage segregation, visual warnings, and clinical verification layers apply to every high-alert substance across all care units.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "2.0 Five Rights & Independent Dual Nurse Verification",
                    "content": [
                        "Prior to administering any high-alert medication, two licensed nurses must independently verify: (1) right patient using two identifiers, (2) right drug, (3) right dose and concentration, (4) right route, and (5) right time and rate. Both clinicians must enter their credentials in the eMAR dual sign-off module prior to administration.",
                    ],
                },
            ],
            # Page 2
            [
                {
                    "type": "section",
                    "heading": "3.0 Look-Alike / Sound-Alike (LASA) and Tall-Man Labeling",
                    "content": [
                        "Pharmacy labels, order entry systems, and automated dispensing cabinets (ADC) must utilize FDA/ISMP Tall-Man lettering (e.g., DOBUTamine vs. DOPamine, hydrOXYzine vs. hydrALAZINE, vinBLAStine vs. vinCRIStine). Distinct visual color cues must highlight high-potency formulations.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "4.0 Automated Dispensing Cabinet (ADC) Lock-Out Constraints",
                    "content": [
                        "ADCs must maintain strict storage partition constraints. Undiluted potassium chloride vials (> 20 mEq) are completely locked out and barred from floor stock. Concentrated sodium chloride (> 0.9%) and sterile water for injection vials > 100 mL are restricted to the central pharmacy IV cleanroom.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Drug Formulation", "Storage Restriction", "Permitted Unit Location", "Access Verification"],
                    "rows": [
                        ["Potassium Chloride Vials", "Locked out from floor stock", "Central IV Cleanroom only", "Pharmacist double verification"],
                        ["Neuromuscular Blockers", "Segregated locked red lidded box", "OR and ICU cabinets only", "Dual-nurse sign-off required"],
                        ["Concentrated NaCl (> 0.9%)", "Cleanroom compounding only", "Main Inpatient Pharmacy", "Batch tracking log entry"],
                        ["Oral Methotrexate", "Dosed weekly; high-alert icon", "Oncology units / Central Rx", "Independent pharmacist oncology check"],
                    ],
                },
            ],
            # Page 3
            [
                {
                    "type": "section",
                    "heading": "5.0 Smart Infusion Pump Dose Error Reduction System (DERS)",
                    "content": [
                        "All continuous intravenous infusions of high-alert medications must be delivered via smart infusion pumps loaded with the approved Drug Error Reduction System (DERS) drug library. Pump drug library compliance must be maintained at ≥ 98% hospital-wide. Overriding a hard dose limit is strictly prohibited by pump software.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "6.0 Intravenous Insulin Protocol and Glycemic Monitoring",
                    "content": [
                        "Continuous regular insulin infusions must follow the validated hospital glycemic control protocol. The maximum initial infusion rate must not exceed 10 units/hour without written authorization from an endocrinologist or intensivist. Bedside point-of-care capillary blood glucose must be measured every 60 minutes while on active titration.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [105, 115, 120, 160],
                    "header": ["Medication Name", "Standard Concentration", "Soft Dose Upper Limit", "Hard Max Limit (No Override)"],
                    "rows": [
                        ["Regular Insulin IV", "100 units in 100 mL NS (1 u/mL)", "8 units / hour", "10 units/hour (specialist auth)"],
                        ["Unfractionated Heparin", "25,000 units in 250 mL D5W", "1,800 units / hour", "2,500 units / hour hard stop"],
                        ["Norepinephrine (Levophed)", "16 mcg / mL in D5W or NS", "30 mcg / minute", "40 mcg / minute hard stop"],
                        ["Propofol (Diprivan)", "10 mg / mL (1000 mg in 100 mL)", "50 mcg / kg / minute", "70 mcg / kg / minute hard stop"],
                    ],
                },
            ],
            # Page 4
            [
                {
                    "type": "section",
                    "heading": "7.0 Anticoagulation Management: Heparin and Low Molecular Weight Heparin",
                    "content": [
                        "Therapeutic unfractionated heparin infusions require baseline CBC, PT/INR, and aPTT prior to initiation. Anticoagulation monitoring must achieve a target therapeutic aPTT window of 60 to 85 seconds (or anti-Xa 0.3 to 0.7 IU/mL). aPTT must be drawn 6 hours after any rate titration until two consecutive therapeutic values are documented.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "8.0 Concentrated Electrolytes and Neuromuscular Blockers",
                    "content": [
                        "Intravenous push administration of concentrated potassium chloride is absolutely prohibited under all circumstances. Neuromuscular blocking agents (rocuronium, vecuronium, succinylcholine) must only be administered to intubated and mechanically ventilated patients with continuous pulse oximetry and capnography.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 125, 150],
                    "header": ["High-Alert Drug Class", "Therapeutic Monitoring", "Clinical Goal Range", "Emergency Antidote"],
                    "rows": [
                        ["Heparin (Unfractionated)", "aPTT every 6 hours", "60 to 85 seconds", "Protamine sulfate (1 mg / 100 u)"],
                        ["Warfarin (Coumadin)", "Daily INR check", "INR 2.0 to 3.0 (target 2.5)", "Vitamin K 10 mg IV / 4-Factor PCC"],
                        ["Opioid Infusions (PCA)", "Continuous capnography & SpO2", "EtCO2 35-45 mmHg, RR > 10", "Naloxone 0.4 mg IV rapid push"],
                        ["Magnesium Sulfate IV", "Deep tendon reflexes, respiration", "Serum Mg 4.8 to 8.4 mg/dL", "Calcium gluconate 1 g IV over 10m"],
                    ],
                },
            ],
            # Page 5
            [
                {
                    "type": "section",
                    "heading": "9.0 Personal Protective Equipment: Chemotherapy Glove Handling",
                    "content": [
                        "Handling and administration of hazardous antineoplastic medications requires specialized PPE. Personnel must wear chemotherapy-tested nitrile gloves meeting ASTM D6978 standards. Double-gloving is mandatory: the inner glove worn under the gown cuff and the outer glove over the cuff. Gloves must be inspected for tears and replaced every 30 minutes of continuous handling.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "10.0 Emergency Reversal Agents and Rapid Antidote Stock",
                    "content": [
                        "Emergency reversal agents must be stocked in every inpatient automated dispensing cabinet: Naloxone 0.4 mg IV for acute opioid-induced respiratory depression, Protamine sulfate (1 mg per 100 units of heparin administered within the preceding 2 hours), and Vitamin K (phytonadione) 10 mg IV for life-threatening warfarin-associated coagulopathy.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 120, 155],
                    "header": ["Reversal Antidote", "Target Toxicity", "Emergency Dose", "Administration Route"],
                    "rows": [
                        ["Naloxone HCl", "Opioid respiratory depression", "0.4 mg IV push (titrate q2-3m)", "Direct IV push or IM injection"],
                        ["Protamine Sulfate", "Heparin over-anticoagulation", "1 mg per 100 u heparin (max 50 mg)", "Slow IV infusion over 10 minutes"],
                        ["Phytonadione (Vitamin K)", "Warfarin-induced major bleed", "10 mg IV in 50 mL NS", "Slow IV piggyback over 20 minutes"],
                        ["Flumazenil", "Benzodiazepine sedation", "0.2 mg IV over 30 seconds", "IV push; repeat 0.1 mg q60s (max 1mg)"],
                    ],
                },
            ],
            # Page 6
            [
                {
                    "type": "section",
                    "heading": "11.0 eMAR Documentation Standards and Discrepancy Logging",
                    "content": [
                        "Every medication administration must be documented in the eMAR using barcode medication administration (BCMA) scanning. Dual clinician signatures are required in the eMAR within 5 minutes prior to initiating or adjusting the rate of any high-alert medication infusion. Unscanned doses must have a clinical override reason documented.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "12.0 Adverse Drug Event Reporting and Root Cause Analysis Escalation",
                    "content": [
                        "Any medication error that reaches the patient or results in harm must be reported immediately to the attending physician and logged in the patient safety incident reporting system. When an error results in serious patient harm (Category G, H, or I), the charge nurse must notify the Pharmacy Director and Patient Safety Officer within 60 minutes to initiate a formal root cause analysis.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [105, 125, 110, 160],
                    "header": ["Error Severity (NCC MERP)", "Clinical Impact", "Notification Window", "Investigation Authority"],
                    "rows": [
                        ["Category C - D", "Reached patient; no harm", "Within 12 hours", "Nurse Manager & Staff Pharmacist"],
                        ["Category E - F", "Temporary harm / intervention", "Within 4 hours", "Medication Safety Officer"],
                        ["Category G - H", "Permanent harm / life-support", "within 60 minutes", "Pharmacy Director & Safety Officer"],
                        ["Category I", "Patient fatality from error", "Immediate (within 15 minutes)", "Chief Medical Officer & CEO / RCA"],
                    ],
                },
            ],
            # Page 7
            [
                {
                    "type": "section",
                    "heading": "13.0 Patient Discharge Medication Counseling and High-Risk Drug Education",
                    "content": [
                        "Patients discharged on high-alert medications (oral anticoagulants, insulin, opioids) must receive one-on-one counseling from a clinical pharmacist. Patients must receive written education brochures in their primary language and demonstrate correct insulin pen priming or anticoagulant dose scheduling prior to discharge.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "14.0 Document Administration and P&T Committee Ratification",
                    "content": [
                        "This SOP is reviewed annually by the Medication Safety Subcommittee and endorsed by the Pharmacy and Therapeutics (P&T) Committee.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [70, 85, 195, 150],
                    "header": ["Version", "Effective Date", "Summary of Revisions", "Approved Authority"],
                    "rows": [
                        ["v1.0", "2024-01-01", "Initial high-alert medication safety release", "P&T Committee"],
                        ["v2.0", "2025-01-01", "Standardized smart pump DERS hard limits", "Medication Safety Council"],
                        ["v3.0", "2026-01-01", "Updated ASTM D6978 chemo glove and insulin protocols", "Pharmacy Director"],
                    ],
                },
            ],
        ],
    },
    "patient_consent": {
        "filename": "sop_patient_consent.pdf",
        "doc_id": "SOP-CON-2026-05",
        "department": "Medical Staff Affairs & Legal Counsel",
        "subtitle": "METROPOLITAN HEALTH SYSTEM — CLINICAL GOVERNANCE",
        "title": "STANDARD OPERATING PROCEDURE: INFORMED CONSENT FOR CLINICAL PROCEDURES AND RESEARCH",
        "effective_date": "2026-01-01",
        "review_cycle": "Annual",
        "pages": [
            # Page 1
            [
                {
                    "type": "section",
                    "heading": "1.0 Ethical Principles and Legal Framework",
                    "content": [
                        "Informed consent is an ethical and legal mandate rooted in patient autonomy. Patients possess the right to make decisions regarding medical interventions based on adequate disclosure of diagnoses, risks, benefits, and reasonable alternatives, including the option of declining treatment.",
                        "Consent is an interactive clinical dialogue rather than a transactional document signing. Clinicians must facilitate an open conversation allowing patients to evaluate potential trade-offs and arrive at decisions aligned with personal values.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "2.0 Elements of Informed Consent Disclosure",
                    "content": [
                        "The consenting clinician must discuss in plain language: (1) the nature of the condition, (2) the proposed procedure, (3) common and serious risks, (4) anticipated clinical benefits, (5) available alternative treatments, and (6) the prognosis if no treatment is undertaken. The patient must have the opportunity to ask questions.",
                    ],
                },
            ],
            # Page 2
            [
                {
                    "type": "section",
                    "heading": "3.0 Provider Responsibilities and Non-Delegation Rule",
                    "content": [
                        "The licensed practitioner performing the procedure retains non-delegable legal responsibility for obtaining informed consent. Nurses, trainees, or administrative staff may not obtain informed consent; their role is strictly limited to witnessing the patient's signature on the pre-completed consent form.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "4.0 Patient Decision-Making Capacity Evaluation",
                    "content": [
                        "Every adult patient is presumed to possess decision-making capacity unless demonstrated otherwise. Clinical capacity requires that the patient can: (1) understand relevant medical facts, (2) appreciate how the facts apply to their situation, (3) reason logically about choices, and (4) clearly communicate a stable choice.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 120, 115, 150],
                    "header": ["Capacity Component", "Clinical Evaluation Question", "Passing Clinical Criteria", "Responsible Evaluator"],
                    "rows": [
                        ["Understanding", "Can patient repeat diagnosis & plan?", "Explains core medical concepts", "Attending Proceduralist"],
                        ["Appreciation", "Does patient see how it affects them?", "Acknowledges personal illness", "Attending Proceduralist"],
                        ["Reasoning", "Why choose this option over others?", "Articulates rational trade-offs", "Attending / Psych Consult"],
                        ["Communication", "Can patient state a consistent choice?", "Stable choice over repeated interviews", "Attending Proceduralist"],
                    ],
                },
            ],
            # Page 3
            [
                {
                    "type": "section",
                    "heading": "5.0 Validity Period and Re-Verification Before Surgery",
                    "content": [
                        "A signed informed consent form remains valid for a maximum of 30 days prior to an elective procedure, provided there has been no material change in the patient's condition or procedure plan. On the day of surgery, the operative team must conduct a bedside re-verification within 24 hours prior to incision.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "6.0 Surrogate Decision-Maker Priority Order",
                    "content": [
                        "When an adult patient lacks decision-making capacity, clinicians must identify a surrogate decision maker in strict accordance with statutory priority: (1) court-appointed Legal guardian with healthcare authority, (2) designated Healthcare proxy / Durable Power of Attorney, (3) Legal spouse, (4) Adult child (≥ 18 years), (5) Parent, (6) Adult sibling, and (7) Nearest living adult relative.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [85, 125, 130, 160],
                    "header": ["Priority Tier", "Surrogate Classification", "Legal Documentation Required", "Clinical Authority Limits"],
                    "rows": [
                        ["Rank 1", "Court-Appointed Guardian", "Certified Letters of Guardianship", "Full medical decisions per court order"],
                        ["Rank 2", "Healthcare Proxy / DPOA", "Executed Health Care Proxy Form", "Active only upon incapacity determination"],
                        ["Rank 3", "Legal spouse", "Marriage certificate / EMR record", "Routine and major surgical decisions"],
                        ["Rank 4", "Adult child (≥ 18 yrs)", "Birth certificate / ID verification", "Consensus among siblings preferred"],
                        ["Rank 5", "Custodial Parent", "Government photo identification", "Full authority for adult dependent"],
                    ],
                },
            ],
            # Page 4
            [
                {
                    "type": "section",
                    "heading": "7.0 Pediatric and Minor Patient Assent Rules",
                    "content": [
                        "For minor patients (< 18 years), informed consent must be provided by a custodial parent or legal guardian. Minors aged 7 to 17 years must be included in the discussion and provide developmentally appropriate verbal or written assent. Emancipated minors may consent independently.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "8.0 Emergency Treatment Exception Protocol",
                    "content": [
                        "Under the emergency exception doctrine, life-saving or limb-preserving medical interventions may proceed without express consent when: (1) the patient is incapacitated, (2) no surrogate is immediately reachable, and (3) immediate intervention is required within 15 minutes to avert imminent death or severe permanent bodily impairment. Two physicians must document the emergency justification in the EMR.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Emergency Parameter", "Clinical Requirement", "EMR Documentation Step", "Verification Standard"],
                    "rows": [
                        ["Imminent Threat", "Limb or life hazard within 15 minutes", "Document acute physiological decline", "Emergency Physician / Surgeon"],
                        ["Surrogate Unreachable", "Documented phone calls to contacts", "Log 2 unsuccessful attempts with time", "Social Work / Nursing Staff"],
                        ["Dual-Physician Sign-off", "Two licensed MDs independent review", "Co-sign Emergency Treatment Note", "Attending + Independent MD"],
                        ["Post-Emergent Notification", "Disclose interventions to surrogate", "Document in EMR within 12 hours", "Primary Attending Physician"],
                    ],
                },
            ],
            # Page 5
            [
                {
                    "type": "section",
                    "heading": "9.0 Clinical Research and Experimental Therapy Consent",
                    "content": [
                        "Participation in clinical research requires separate, unbundled informed consent reviewed and approved by the Institutional Review Board (IRB). Coercion or undue influence is strictly prohibited. Research consent forms must disclose financial conflicts of interest and state that refusing will not compromise clinical care.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "10.0 Language Access, Interpreters, and Communication Barriers",
                    "content": [
                        "Patients with limited English proficiency (LEP) or sensory impairments must be provided with a certified medical interpreter in-person or via video remote interpreting (VRI). Family members, friends, or bilingual staff without medical interpreter certification are strictly prohibited from interpreting consent discussions.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 120, 155],
                    "header": ["Communication Need", "Mandated Service Modality", "Certification Standard", "Prohibited Practice"],
                    "rows": [
                        ["Limited English (LEP)", "Certified Medical Interpreter (VRI/In-person)", "NBCMI or CCHI Certified", "Ad hoc family/friend translation"],
                        ["Deaf / Hard of Hearing", "Certified ASL Medical Interpreter", "RID / NAD Certified Interpreter", "Lip-reading assumptions"],
                        ["Cognitive Impairment", "Surrogate decision-maker dialogue", "Documented legal authority", "Proceeding without legal surrogate"],
                        ["Blind / Visually Impaired", "Braille / Large print / Verbal read-back", "Witnessed verbal consent recording", "Unassisted signature on standard form"],
                    ],
                },
            ],
            # Page 6
            [
                {
                    "type": "section",
                    "heading": "11.0 EMR Documentation and Verification Timing",
                    "content": [
                        "The signed consent document must be scanned into the EMR document repository or electronically signed via digital signature pad at least 60 minutes prior to surgical transport. Proceduralists handling paper consent forms in treatment areas must remove clinical gloves before handling physical charts. The pre-procedure 'Time-Out' checklist requires verifying the consent form matches the surgical schedule and patient wristband.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "12.0 Ethical Disputes, Refusals, and Legal Risk Escalation",
                    "content": [
                        "When a competent patient refuses life-sustaining treatment, or when surrogates disagree irreconcilably, the clinical team must immediately notify Hospital Risk Management and On-Call Legal Counsel. An emergency meeting of the Hospital Ethics Committee must be convened within 6 hours to provide ethical guidance.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Dispute Scenario", "First Clinical Responder", "Escalation Target", "Mandatory Action Window"],
                    "rows": [
                        ["Surrogate Disagreement", "Unit Care Coordinator", "Hospital Ethics Committee", "Convene review within 6 hours"],
                        ["Refusal of Life-Saving Tx", "Attending Physician", "Risk Management & Legal Counsel", "Immediate consult (within 1 hour)"],
                        ["Unrepresented Incapacitated", "Case Management Director", "Hospital Guardianship Panel", "Court petition within 48 hours"],
                        ["Suspected Coercion", "Bedside Registered Nurse", "Patient Safety Officer & Social Work", "Suspension of procedure immediately"],
                    ],
                },
            ],
            # Page 7
            [
                {
                    "type": "section",
                    "heading": "13.0 Revocation of Consent and Treatment Termination",
                    "content": [
                        "A patient or authorized surrogate may revoke consent at any time, verbally or in writing, prior to the initiation of anesthesia or surgical incision. Upon revocation, all preparations must cease immediately, and the proceduralist must document the revocation in the EMR.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "14.0 Institutional Governance and Medical Executive Endorsements",
                    "content": [
                        "This policy is reviewed annually by the Medical Staff Rules and Regulations Committee and endorsed by the Medical Executive Committee.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [70, 85, 195, 150],
                    "header": ["Version", "Effective Date", "Summary of Revisions", "Approved Authority"],
                    "rows": [
                        ["v1.0", "2024-01-01", "Initial clinical informed consent governance", "Medical Staff Executive"],
                        ["v2.0", "2025-01-01", "Clarified non-delegation and emergency exception", "Legal Counsel Office"],
                        ["v3.0", "2026-01-01", "Updated 30-day elective validity and interpreter standards", "Chief Medical Officer"],
                    ],
                },
            ],
        ],
    },
    "hand_hygiene": {
        "filename": "sop_hand_hygiene.pdf",
        "doc_id": "SOP-HYG-2026-06",
        "department": "Infection Prevention & Hospital Epidemiology",
        "subtitle": "METROPOLITAN HEALTH SYSTEM — CLINICAL POLICY & PROCEDURE",
        "title": "STANDARD OPERATING PROCEDURE: HAND HYGIENE PROTOCOLS AND SANITIZATION BENCHMARKS",
        "effective_date": "2026-01-01",
        "review_cycle": "Annual",
        "pages": [
            # Page 1
            [
                {
                    "type": "section",
                    "heading": "1.0 Purpose and Clinical Infection Prevention Rationale",
                    "content": [
                        "Hand hygiene is the single most effective measure to prevent healthcare-associated infections (HAIs) and antimicrobial resistance. This SOP mandates hand hygiene procedures, compliance benchmarks, and audit mechanisms across all hospital inpatient and outpatient departments.",
                        "Pathogen transmission occurs predominantly via transiently colonized hands of healthcare workers. Systematic execution of evidence-based hand cleaning eliminates bacterial colonization and breaks the cycle of patient-to-patient cross-contamination.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "2.0 Regulatory Mandates and CDC/WHO Alignment",
                    "content": [
                        "All hospital employees, medical staff, allied health professionals, and volunteers must comply with CDC Guideline for Hand Hygiene in Healthcare Settings and the WHO Multimodal Hand Hygiene Improvement Strategy. Institutional target compliance is ≥ 95% across all clinical units.",
                    ],
                },
            ],
            # Page 2
            [
                {
                    "type": "section",
                    "heading": "3.0 The WHO Five Moments for Hand Hygiene",
                    "content": [
                        "Hand hygiene must be performed during the WHO Five Moments: (1) before touching a patient, (2) before clean/aseptic procedures, (3) after body fluid exposure risk, (4) after touching a patient, and (5) after touching patient surroundings.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "4.0 Alcohol-Based Hand Rub (ABHR) Technique and Volume",
                    "content": [
                        "Alcohol-based hand rub containing 70% to 80% ethyl alcohol is the preferred method for routine hand antisepsis when hands are not visibly soiled. Staff must apply 3 to 5 mL of rub into the palm and rub all surfaces of hands and fingers vigorously for 20 to 30 seconds until dry.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [105, 115, 120, 160],
                    "header": ["WHO Moment", "Clinical Trigger", "Pathogen Defense Goal", "Approved Cleansing Modality"],
                    "rows": [
                        ["1. Before Patient Contact", "Approaching bedside zone", "Protect patient from staff flora", "ABHR (3 to 5 mL) or Soap & Water"],
                        ["2. Before Aseptic Task", "Starting IV or catheter line", "Prevent pathogen entry into tissue", "ABHR or Chlorhexidine scrub"],
                        ["3. After Body Fluid Exposure", "Emptying Foley or drain bag", "Protect staff & hospital environment", "Mandatory Soap & Water if gross fluid"],
                        ["4. After Patient Contact", "Exiting immediate bedside", "Prevent carriage to other patients", "ABHR (3 to 5 mL) for 20-30s"],
                        ["5. After Surroundings", "Touching IV pump or bedrail", "Decontaminate fomite transfer", "ABHR (3 to 5 mL) until dry"],
                    ],
                },
            ],
            # Page 3
            [
                {
                    "type": "section",
                    "heading": "5.0 Handwashing with Antimicrobial Soap and Running Water",
                    "content": [
                        "Handwashing with soap and running water is mandatory when hands are visibly soiled with blood or bodily fluids, after using the restroom, and following care of patients with suspected or confirmed spore-forming organisms (Clostridioides difficile, Bacillus anthracis) or norovirus. Hands must be scrubbed vigorously for 40 to 60 seconds covering palms, backs, interdigital spaces, and wrists, then dried thoroughly with single-use paper towels.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "6.0 C. Difficile and Spore-Forming Pathogen Specifics",
                    "content": [
                        "Alcohol hand sanitizers do not destroy bacterial spores. Therefore, alcohol-based hand rub is strictly prohibited as the sole cleansing agent when exiting rooms under Enteric Contact Precautions. Mechanical friction with soap and water is required to physically remove spores.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Pathogen Category", "Cleansing Agent Mandate", "Minimum Scrub Duration", "Restricted Practice"],
                    "rows": [
                        ["C. difficile / Spores", "Antimicrobial Soap & Water", "40 to 60 seconds", "Alcohol-based rub strictly banned"],
                        ["Norovirus Outbreak", "Soap & Water preferred", "40 to 60 seconds", "Routine rub without water rinse"],
                        ["MRSA / VRE Flora", "Alcohol-Based Hand Rub", "20 to 30 seconds until dry", "Wiping wet rub with paper towel"],
                        ["Blood / Body Fluid Splash", "Antimicrobial Soap & Water", "Full 60 seconds scrub", "Delaying wash past immediate exit"],
                    ],
                },
            ],
            # Page 4
            [
                {
                    "type": "section",
                    "heading": "7.0 Glove Use Principles and Decontamination Boundaries",
                    "content": [
                        "The use of gloves does not replace the requirement for hand hygiene. Healthcare personnel must decontaminate hands immediately prior to donning examination gloves and immediately after glove removal. Gloves must be changed between separate tasks on the same patient if moving from a contaminated body site to a clean body site. Reusing or washing disposable medical examination gloves is strictly prohibited.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "8.0 Fingernail Standards, Jewelry, and Skin Integrity Guidelines",
                    "content": [
                        "Natural fingernail tips must be kept clean and trimmed to a maximum length of 0.25 inches (6 mm). Artificial fingernails, tips, wraps, appliques, and gel polish are strictly prohibited for all healthcare workers providing direct patient care. One plain wedding band is permitted; wristwatches and dangling bracelets must be removed during direct clinical interventions.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [110, 115, 115, 160],
                    "header": ["Grooming Parameter", "Institutional Limit", "Target Care Population", "Infection Rationale"],
                    "rows": [
                        ["Fingernail Length", "Maximum 0.25 inches (6 mm)", "All direct care staff", "Harbors subungual gram-negative rods"],
                        ["Artificial Nails / Wraps", "Strictly prohibited", "Inpatient and surgical personnel", "Associated with fungal/bacterial outbreaks"],
                        ["Rings / Hand Jewelry", "One plain band allowed", "Clinical providers", "Impairs glove integrity and hand washing"],
                        ["Wristwatches / Bracelets", "Removed for clinical tasks", "ICU and Procedural staff", "Prevents thorough wrist scrubbing"],
                    ],
                },
            ],
            # Page 5
            [
                {
                    "type": "section",
                    "heading": "9.0 Dispenser Placement, Maintenance, and Supply Levels",
                    "content": [
                        "Wall-mounted touchless alcohol rub dispensers must be installed at the entrance to every patient room, inside every room, and at point-of-care workstations. Facilities staff must inspect dispensers daily during morning rounds. Any empty or malfunctioning dispenser must be refilled or repaired within 60 minutes of notification.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "10.0 Quality Surveillance: The Secret Shopper Observation Program",
                    "content": [
                        "Hand hygiene compliance is audited using the direct observational 'Secret Shopper' methodology by trained Infection Prevention Observers. Observers must record at least 30 random observations per clinical unit per month covering day, evening, and night shifts.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Audit Dimension", "Sampling Quota", "Auditing Role", "Compliance Target"],
                    "rows": [
                        ["Inpatient Unit Observation", "30 observations / unit / month", "Infection Prevention Observer", "≥ 95% compliance target"],
                        ["Emergency Department", "50 observations / month", "Trained Peer Champion", "≥ 95% compliance target"],
                        ["Intensive Care Units", "40 observations / ICU / month", "Quality Specialist", "≥ 98% strict compliance target"],
                        ["Surgical Scrub Verification", "100% of scrub staff audited", "Operating Room Charge RN", "Full surgical scrub compliance"],
                    ],
                },
            ],
            # Page 6
            [
                {
                    "type": "section",
                    "heading": "11.0 Monthly Unit Reporting and EMR Compliance Logging",
                    "content": [
                        "Unit compliance percentages are compiled monthly and posted on the Infection Control Quality Dashboard by the 5th business day of each month. Hand hygiene observation data is logged in the hospital safety reporting portal and correlated with unit catheter-associated urinary tract infection (CAUTI) and central line-associated bloodstream infection (CLABSI) rates.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "12.0 Corrective Action Plans and Leadership Escalation",
                    "content": [
                        "Units achieving ≥ 95% compliance receive institutional quality commendations. Any inpatient unit scoring < 85% compliance for two consecutive cycles must submit a formal Corrective Action Plan (CAP) to the Chief Nursing Officer and Infection Control Committee within 14 days, with mandatory re-training of unit staff.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [105, 125, 110, 160],
                    "header": ["Performance Tier", "Compliance Score", "Administrative Consequence", "Follow-up Timeline"],
                    "rows": [
                        ["Gold Tier", "≥ 95% compliance", "Excellence commendation", "Standard monthly surveillance"],
                        ["Silver Tier", "90% to 94.9%", "Unit manager internal coaching", "Bi-weekly observer sampling"],
                        ["Warning Tier", "85% to 89.9%", "Written memo from Quality Chair", "Weekly observation rounds"],
                        ["Escalation Tier", "scoring < 85% compliance", "Escalation to Chief Nursing Officer", "Mandatory staff retraining in 14 days"],
                    ],
                },
            ],
            # Page 7
            [
                {
                    "type": "section",
                    "heading": "13.0 Occupational Dermatitis and Skin Health Protection",
                    "content": [
                        "Healthcare workers experiencing contact dermatitis or skin breakdown from frequent hand hygiene must be referred to Occupational Health within 48 hours for evaluation and provision of hypoallergenic, fragrance-free moisturizing lotions and barrier creams.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "14.0 Institutional Governance and Quality Council Ratification",
                    "content": [
                        "This SOP is reviewed annually by the Hospital Infection Prevention Committee and approved by the Quality and Safety Executive Council.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [70, 85, 195, 150],
                    "header": ["Version", "Effective Date", "Summary of Revisions", "Approved Authority"],
                    "rows": [
                        ["v1.0", "2024-01-01", "Initial multimodal hand hygiene standard", "Infection Control Panel"],
                        ["v2.0", "2025-01-01", "Adopted WHO 5 Moments secret shopper audits", "Hospital Quality Council"],
                        ["v3.0", "2026-01-01", "Reinforced C. diff soap scrubbing and nail rules", "Chief Nursing Officer"],
                    ],
                },
            ],
        ],
    },
    "fall_prevention": {
        "filename": "sop_fall_prevention.pdf",
        "doc_id": "SOP-FAL-2026-07",
        "department": "Nursing Administration & Patient Safety",
        "subtitle": "METROPOLITAN HEALTH SYSTEM — CLINICAL POLICY & PROCEDURE",
        "title": "STANDARD OPERATING PROCEDURE: INPATIENT FALL RISK ASSESSMENT AND POST-FALL PROTOCOL",
        "effective_date": "2026-01-01",
        "review_cycle": "Annual",
        "pages": [
            # Page 1
            [
                {
                    "type": "section",
                    "heading": "1.0 Mission and Fall Reduction Benchmarks",
                    "content": [
                        "Patient falls represent one of the most common adverse events in acute care hospitals. This standard operating procedure outlines the mandatory fall risk assessment, targeted environmental interventions, and rapid post-fall clinical evaluation to prevent fall-related injuries.",
                        "The hospital institutional fall benchmark is < 2.5 falls per 1,000 patient days, with zero falls resulting in moderate to severe harm. Multi-disciplinary engagement involving nursing, physical therapy, and clinical pharmacy is required to achieve this standard.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "2.0 Scope and Multi-Disciplinary Responsibilities",
                    "content": [
                        "This protocol applies to all adult inpatient medical, surgical, intensive care, and psychiatric units. Nurses, physicians, physical therapists, occupational therapists, and patient care technicians share active responsibility for maintaining fall safety precautions.",
                    ],
                },
            ],
            # Page 2
            [
                {
                    "type": "section",
                    "heading": "3.0 Morse Fall Scale (MFS) Scoring Methodology",
                    "content": [
                        "Fall risk must be evaluated using the validated Morse Fall Scale (MFS), which scores six variables: history of falling, secondary diagnosis, ambulatory aid, IV or heparin lock, gait/transferring, and mental status. Patients are stratified into three categories: Low risk (0 to 24), Moderate risk (25 to 50), and High risk (≥ 51).",
                    ],
                },
                {
                    "type": "section",
                    "heading": "4.0 Timing and Frequency of Fall Risk Screenings",
                    "content": [
                        "An initial MFS assessment must be completed within 4 hours of inpatient admission. Reassessments must be documented every 12-hour nursing shift, upon transfer between units, following any change in clinical or mental status, and immediately following any patient fall.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [110, 115, 115, 160],
                    "header": ["Morse Scale Item", "Clinical Assessment Condition", "Assigned Value", "Documentation Rule"],
                    "rows": [
                        ["1. History of Falls", "No falls in prior 3 months / Yes", "0 or 25 points", "Check EMR and family report"],
                        ["2. Secondary Diagnosis", "Only 1 active diagnosis / ≥ 2", "0 or 15 points", "Review active problem list"],
                        ["3. Ambulatory Aid", "None/Bedrest vs Crutches/Walker vs Furniture", "0 vs 15 vs 30 points", "Direct physical observation"],
                        ["4. IV Line / Saline Lock", "No IV access / Active IV cannula", "0 or 20 points", "Verify peripheral or central line"],
                        ["5. Gait / Transferring", "Normal vs Weak vs Impaired", "0 vs 10 vs 20 points", "Observe unassisted bed rise"],
                        ["6. Mental Status", "Knows own limits / Overestimates", "0 or 15 points", "Ask patient how they plan to walk"],
                    ],
                },
            ],
            # Page 3
            [
                {
                    "type": "section",
                    "heading": "5.0 Universal Environmental Fall Safety Controls",
                    "content": [
                        "Universal fall precautions must be maintained for all inpatients: bed maintained in the lowest position with casters locked, top two side rails raised, personal call bell within 12 inches of patient reach, pathway to the bathroom clear of trip hazards, and non-skid footwear worn during any ambulation.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "6.0 Targeted Interventions for Moderate and High-Risk Patients",
                    "content": [
                        "Patients scoring in the high-risk category (MFS ≥ 51) require active barrier safeguards: placement of a Yellow alert wristband, yellow non-skid socks, activation of a bed/chair exit alarm, bedside commode within 3 feet, and scheduled toileting assistance every 2 hours.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [90, 105, 135, 170],
                    "header": ["Risk Tier", "MFS Score", "Mandatory Visual Signs", "Active Nursing Safety Protocols"],
                    "rows": [
                        ["Low Risk", "0 to 24 points", "Standard hospital ID band", "Universal precautions, call bell within reach"],
                        ["Moderate Risk", "25 to 50 points", "Yellow door sign, non-skid socks", "Assisted ambulation, hourly rounding"],
                        ["High risk (≥ 51)", "≥ 51 points", "Yellow alert wristband, yellow non-skid socks", "Bed alarm active, commode 3 ft, q2h toileting"],
                        ["Very High / Delirium", "≥ 75 points", "Yellow band, 1:1 sitter review", "Low-bed with floor mat, continuous observer"],
                    ],
                },
            ],
            # Page 4
            [
                {
                    "type": "section",
                    "heading": "7.0 Assistive Equipment and Bed Exit Alarm Calibration",
                    "content": [
                        "Pressure-sensitive bed and chair exit alarms must be tested for audible sound and transmitter function at the beginning of each nursing shift. Patient care technicians must respond immediately to an activated bed alarm within 30 seconds.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "8.0 Medication Review for Fall-Risk-Increasing Drugs (FRIDs)",
                    "content": [
                        "A clinical pharmacist must perform a medication review within 24 hours of admission for high-risk fall patients. Sedatives, hypnotics, antipsychotics, benzodiazepines, antihypertensives, and diuretics must be reviewed for deprescribing or dosage reduction.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 120, 155],
                    "header": ["FRID Drug Class", "Representative Agents", "Fall Mechanism", "Clinical Pharmacist Action"],
                    "rows": [
                        ["Sedative / Hypnotics", "Zolpidem, temazepam", "Morning grogginess / ataxia", "Deprescribe; trial non-drug sleep aid"],
                        ["Benzodiazepines", "Lorazepam, alprazolam", "Impaired motor coordination", "Taper dose; evaluate delirium risk"],
                        ["Antihypertensives", "Lisinopril, amlodipine", "Orthostatic hypotension", "Check sitting/standing BP; adjust dose"],
                        ["Loop Diuretics", "Furosemide, bumetanide", "Urgent nocturia / volume loss", "Schedule morning administration only"],
                    ],
                },
            ],
            # Page 5
            [
                {
                    "type": "section",
                    "heading": "9.0 Immediate Post-Fall Assessment and Immobilization",
                    "content": [
                        "If a patient falls, staff must not move the patient until a registered nurse completes an immediate primary survey assessing airway, breathing, circulation, spinal pain, limb deformity, and neurological status. Caregivers must don clean examination gloves before managing abrasions or lacerations.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "10.0 Post-Fall Neurological Checks and Emergency Head Imaging",
                    "content": [
                        "For any patient who sustains an unwitnessed fall, a fall with suspected head impact, or any fall while on therapeutic anticoagulation, neurological vital signs must be recorded every 15 minutes for 1 hour, then hourly for 4 hours. An urgent non-contrast head CT scan must be completed within 60 minutes to rule out intracranial hemorrhage.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [110, 115, 115, 160],
                    "header": ["Post-Fall Interval", "Neurological Parameter", "Targeted Clinical Sign", "Action if Abnormal"],
                    "rows": [
                        ["First 60 minutes", "GCS, pupils, motor every 15m", "Pupillary asymmetry or drop > 2 GCS", "Stat Physician page & RRT"],
                        ["Hours 2 through 4", "Neurological checks hourly", "Vomiting, progressive headache", "Emergent non-contrast head CT"],
                        ["Hours 5 through 24", "Neuro checks every 4 hours", "Altered mental status / lethargy", "Neurosurgical consult dispatch"],
                        ["Anticoagulated Patient", "Mandatory Head CT", "Scan completed within 60 minutes", "Notify Attending & Anticoag Service"],
                    ],
                },
            ],
            # Page 6
            [
                {
                    "type": "section",
                    "heading": "11.0 Incident Documentation in EMR and Safety Portals",
                    "content": [
                        "The primary nurse must document the post-fall assessment, vital signs, physical exam findings, and physician notification in the EMR fall flow-sheet within 2 hours. A safety event report must be submitted in the hospital incident reporting system within 12 hours.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "12.0 Post-Fall Huddle, Root Cause Analysis, and Escalation",
                    "content": [
                        "Within 60 minutes of a fall, the charge nurse must convene an interdisciplinary bedside post-fall huddle. Any fall resulting in moderate to severe injury (fracture, intracranial bleed, surgical intervention) triggers immediate notification of the Patient Safety Officer within 2 hours and an executive Root Cause Analysis (RCA) within 30 days.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Injury Classification", "Clinical Criteria", "Reporting Timeline", "Administrative Review"],
                    "rows": [
                        ["No Injury", "No pain, abrasions, or disability", "within 12 hours in safety portal", "Unit post-fall huddle"],
                        ["Minor Injury", "Skin tear, bruise, ice applied", "within 12 hours in safety portal", "Nurse Manager review"],
                        ["Moderate Injury", "Suture required, non-displaced fracture", "Within 4 hours to Safety Officer", "Comprehensive clinical review"],
                        ["Severe / Sentinel", "Subdural bleed, hip fracture, death", "Immediate (within 2 hours)", "Executive Root Cause Analysis (30d)"],
                    ],
                },
            ],
            # Page 7
            [
                {
                    "type": "section",
                    "heading": "13.0 Physical Restraints as a Measure of Last Resort",
                    "content": [
                        "Physical restraints may only be used as a measure of last resort to prevent imminent falls when all alternative interventions have failed. Restraint orders are valid for a maximum of 24 hours and require physician face-to-face evaluation within 60 minutes of placement.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "14.0 Institutional Governance and Patient Safety Committee Ratification",
                    "content": [
                        "This SOP is reviewed annually by the Falls Prevention Steering Committee and approved by the Chief Medical Officer.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [70, 85, 195, 150],
                    "header": ["Version", "Effective Date", "Summary of Revisions", "Approved Authority"],
                    "rows": [
                        ["v1.0", "2024-01-01", "Initial Morse fall risk standardization", "Nursing Executive Council"],
                        ["v2.0", "2025-01-01", "Standardized urgent 60m head CT for anticoagulated falls", "Patient Safety Committee"],
                        ["v3.0", "2026-01-01", "Mandated yellow wristband and sock visual cues", "Chief Medical Officer"],
                    ],
                },
            ],
        ],
    },
    "blood_transfusion": {
        "filename": "sop_blood_transfusion.pdf",
        "doc_id": "SOP-BLD-2026-08",
        "department": "Transfusion Medicine & Nursing Services",
        "subtitle": "METROPOLITAN HEALTH SYSTEM — CLINICAL POLICY & PROCEDURE",
        "title": "STANDARD OPERATING PROCEDURE: BLOOD COMPONENT TRANSFUSION AND ADVERSE REACTION MANAGEMENT",
        "effective_date": "2026-01-01",
        "review_cycle": "Annual",
        "pages": [
            # Page 1
            [
                {
                    "type": "section",
                    "heading": "1.0 Purpose and Transfusion Governance",
                    "content": [
                        "Blood component therapy carries significant immunological and infectious risks. This standard operating procedure governs the ordering, pre-transfusion compatibility testing, issuing, bedside verification, administration, and adverse reaction management for all blood products.",
                        "Strict chain of custody and rigorous bedside identity checks prevent ABO-incompatible transfusions, which represent life-threatening clinical sentinel events. All clinical staff involved in transfusion care must complete annual transfusion competency verification.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "2.0 Pre-Transfusion Testing and Sample Validity",
                    "content": [
                        "A formal blood bank type and screen sample must be collected in an EDTA pink-top tube. The sample is valid for a maximum 72 hours from the time of collection. Phlebotomists must scan the patient's wristband barcode and verify identity prior to venipuncture; mislabeled tubes are automatically rejected.",
                    ],
                },
            ],
            # Page 2
            [
                {
                    "type": "section",
                    "heading": "3.0 Blood Bank Release and Transport Conditions",
                    "content": [
                        "Blood components are stored in the Blood Bank under strictly controlled temperatures. Units must be transported to clinical floors in validated insulated containers containing coolant packs. Only one unit of packed red blood cells (PRBCs) may be issued per patient at a time.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "4.0 Bedside Dual-Verification Protocol",
                    "content": [
                        "Immediately prior to transfusion, two qualified licensed clinicians (two RNs, or one RN and one MD) must conduct a dual-verification at the patient bedside. Both clinicians must compare: (1) patient full legal name and MRN, (2) unit donation identification number, (3) blood component type, (4) donor ABO and Rh type, (5) recipient ABO and Rh type, and (6) expiration date and time. Both clinicians must sign the verification sheet.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Verification Element", "Source Document 1", "Source Document 2", "Validation Rule"],
                    "rows": [
                        ["Patient Name & MRN", "Patient Barcode Wristband", "Blood Bank Issue Tag", "Exact character-for-character match"],
                        ["Unit Identification No.", "Blood Unit Primary Label", "Transfusion Order Sheet", "Barcode scan and eye match"],
                        ["ABO / Rh Compatibility", "Unit Bag Label", "Laboratory Crossmatch Report", "Compatible donor/recipient match"],
                        ["Unit Expiration Timestamp", "Unit Bag Physical Label", "Issue Documentation Tag", "Current time must not exceed tag"],
                    ],
                },
            ],
            # Page 3
            [
                {
                    "type": "section",
                    "heading": "5.0 Vascular Access, Infusion Sets, and Incompatible Fluids",
                    "content": [
                        "Blood components must be infused through an 18-gauge or 20-gauge peripheral IV catheter (or verified central venous access). A dedicated blood administration tubing set containing a standard 170 to 260-micron filter is mandatory. Blood products must only be infused with 0.9% Sodium Chloride (Normal Saline). Co-infusion with dextrose solutions, lactated Ringer's, or any intravenous medication is strictly prohibited.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "6.0 Rate of Administration and 15-Minute Observation Rule",
                    "content": [
                        "Transfusion must commence within 30 minutes of product release from the Blood Bank and complete within 4 hours maximum from release. The initial transfusion rate must be slow: 2 mL/minute (120 mL/hour) for the first 15 minutes. The bedside nurse must remain with the patient for the entire first 15 minutes to monitor for signs of acute reaction.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 105, 115, 165],
                    "header": ["Component Type", "Unit Volume", "Initial Infusion Rate", "Maximum Infusion Time"],
                    "rows": [
                        ["Packed Red Blood Cells (PRBC)", "250 to 350 mL", "2 mL/min (120 mL/hr) x 15m", "complete within 4 hours"],
                        ["Fresh Frozen Plasma (FFP)", "200 to 250 mL", "5 mL/min (300 mL/hr)", "Complete within 2 hours"],
                        ["Platelets (Apheresis Unit)", "200 to 300 mL", "Run rapidly over 30 to 60m", "Complete within 4 hours"],
                        ["Cryoprecipitate Pool", "100 to 150 mL", "Run rapidly over 15 to 30m", "Complete within 4 hours"],
                    ],
                },
            ],
            # Page 4
            [
                {
                    "type": "section",
                    "heading": "7.0 Patient Monitoring Schedules and Vital Sign Benchmarks",
                    "content": [
                        "Vital signs (temperature, blood pressure, heart rate, respiratory rate, oxygen saturation) must be recorded: (1) baseline within 30 minutes prior to spike, (2) exactly 15 minutes after start of infusion, (3) hourly during active infusion, and (4) at the conclusion of transfusion.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "8.0 Recognition of Acute Transfusion Reactions (AHTR, TRALI, TACO)",
                    "content": [
                        "Staff must maintain high clinical suspicion for transfusion reactions: Acute Hemolytic Transfusion Reaction (AHTR), Febrile Non-Hemolytic Reaction (FNHTR), Transfusion-Related Acute Lung Injury (TRALI), and Transfusion-Associated Circulatory Overload (TACO). A temperature increase ≥ 1.0°C (1.8°F) above baseline or new rigors, back pain, or dyspnea requires immediate cessation.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [110, 115, 115, 160],
                    "header": ["Reaction Type", "Primary Clinical Signs", "Pathophysiological Trigger", "Immediate Nursing Intervention"],
                    "rows": [
                        ["Acute Hemolytic (AHTR)", "Fever, flank pain, red urine, shock", "ABO incompatibility / lysis", "Stop unit; start NS flush; save bag"],
                        ["Febrile Non-Hemolytic", "increase ≥ 1.0°C (1.8°F), rigors", "Cytokines in donor plasma", "Stop unit; notify MD; antipyretic"],
                        ["Allergic / Anaphylactic", "Urticaria, wheezing, hypotension", "IgE antibody response to protein", "Stop unit; administer diphenhydramine/epi"],
                        ["TRALI / TACO", "Acute dyspnea, hypoxia, bilateral infiltrates", "Lung neutrophil priming vs volume overload", "Stop unit; oxygenate; diuretic if TACO"],
                    ],
                },
            ],
            # Page 5
            [
                {
                    "type": "section",
                    "heading": "9.0 Immediate Emergency Reaction Action Steps",
                    "content": [
                        "If an acute reaction is suspected, the nurse must immediately: (1) stop the infusion immediately, (2) disconnect blood tubing at the hub and maintain IV patency with normal saline on fresh tubing, (3) assess ABCs and vital signs, (4) notify the attending physician and Blood Bank, and (5) save the blood bag and tubing for laboratory investigation.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "10.0 Laboratory Investigation and Specimen Collection",
                    "content": [
                        "Following an adverse reaction, the nurse must draw post-reaction blood samples (pink-top EDTA tube and lavender-top tube) from a different venipuncture site and collect a post-transfusion urine sample. The remaining blood product bag, infusion set, and specimens must be sent to the Blood Bank within 30 minutes.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Specimen Required", "Tube / Container Type", "Diagnostic Testing Purpose", "Delivery SLA to Lab"],
                    "rows": [
                        ["Post-Transfusion Blood", "Pink-Top EDTA (6 mL)", "Repeat crossmatch, DAT, ABO check", "Send within 30 minutes"],
                        ["Post-Transfusion CBC", "Lavender-Top EDTA (4 mL)", "Assess hemoglobin & hemolysis drop", "Send within 30 minutes"],
                        ["First Post-Reaction Urine", "Sterile urine cup", "Visual free hemoglobin urinalysis", "Send to lab immediately"],
                        ["Blood Unit & Infusion Set", "Sealed biohazard bag", "Sterility cultures & residual testing", "Hand carry to Blood Bank in 30m"],
                    ],
                },
            ],
            # Page 6
            [
                {
                    "type": "section",
                    "heading": "11.0 EMR Transfusion Flowsheet Documentation",
                    "content": [
                        "All transfusion details must be entered into the EMR transfusion flow-sheet within 30 minutes of transfusion completion. The record must include the unique donation unit number, start and stop times, total volume infused, vital sign log, and dual-clinician signatures.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "12.0 Hemovigilance Committee Review and State Reporting Escalation",
                    "content": [
                        "All reported transfusion reactions are reviewed by the Hospital Transfusion Committee. Suspected acute hemolytic reactions, fatal reactions, or bacterial contamination must be reported to the Blood Bank Medical Director within 15 minutes. Confirmed fatalities must be reported to the FDA Center for Biologics Evaluation and Research (CBER) within 24 hours.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Reaction Severity", "Clinical Definition", "Escalation Notification", "Statutory Reporting"],
                    "rows": [
                        ["Minor Allergic", "Isolated rash or hives", "Blood Bank notification post-event", "Hospital Hemovigilance log"],
                        ["Febrile Non-Hemolytic", "Isolated fever bump < 2°C", "Transfusion service review", "Monthly committee summary"],
                        ["Severe / Life Threatening", "AHTR, TRALI, anaphylactic shock", "within 15 minutes to Medical Director", "State Department of Health (48h)"],
                        ["Transfusion Fatality", "Patient death linked to blood", "Immediate executive leadership page", "FDA CBER notification in 24 hours"],
                    ],
                },
            ],
            # Page 7
            [
                {
                    "type": "section",
                    "heading": "13.0 Massive Transfusion Protocol (MTP) Activation Criteria",
                    "content": [
                        "The Massive Transfusion Protocol (MTP) is activated for exsanguinating hemorrhage anticipated to require > 10 units of PRBCs in 24 hours or > 4 units in 1 hour. Blood products are released in balanced 1:1:1 ratios (6 units PRBCs, 6 units FFP, 1 unit apheresis platelets).",
                    ],
                },
                {
                    "type": "section",
                    "heading": "14.0 Document Administration and Transfusion Committee Approvals",
                    "content": [
                        "This SOP is reviewed biennially by the Transfusion Medicine Service and approved by the Medical Executive Committee.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [70, 85, 195, 150],
                    "header": ["Version", "Effective Date", "Summary of Revisions", "Approved Authority"],
                    "rows": [
                        ["v1.0", "2024-01-01", "Initial transfusion medicine standard", "Transfusion Committee"],
                        ["v2.0", "2025-01-01", "Standardized bedside 2-nurse barcode check", "Nursing Practice Council"],
                        ["v3.0", "2026-01-01", "Updated TRALI diagnostic criteria and MTP 1:1:1", "Transfusion Medical Director"],
                    ],
                },
            ],
        ],
    },
    "emergency_code_response": {
        "filename": "sop_emergency_code_response.pdf",
        "doc_id": "SOP-EMR-2026-09",
        "department": "Emergency Management & Critical Care Medicine",
        "subtitle": "METROPOLITAN HEALTH SYSTEM — EMERGENCY MANAGEMENT POLICY",
        "title": "STANDARD OPERATING PROCEDURE: HOSPITAL-WIDE EMERGENCY CODES AND RESUSCITATION PROTOCOLS",
        "effective_date": "2026-01-01",
        "review_cycle": "Annual",
        "pages": [
            # Page 1
            [
                {
                    "type": "section",
                    "heading": "1.0 Purpose and Emergency Preparedness",
                    "content": [
                        "This standard operating procedure defines hospital emergency code designations, response activations, team member roles, and clinical resuscitation protocols to ensure rapid, coordinated life-saving care across all hospital facilities.",
                        "Standardized emergency codes eliminate ambiguity, minimize communication delays during crises, and ensure predictable staffing and resource allocation across inpatient and ambulatory units.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "2.0 Standardized Hospital Emergency Code Nomenclature",
                    "content": [
                        "The hospital utilizes standardized color-coded emergency alerts: Code Blue (cardiopulmonary arrest), Code Red (fire/smoke), Code Pink (infant abduction), Code White (pediatric medical emergency), Code Yellow (disaster/mass casualty), and Code Silver (active shooter/weapon).",
                    ],
                },
            ],
            # Page 2
            [
                {
                    "type": "section",
                    "heading": "3.0 Code Blue Activation and Team Roles",
                    "content": [
                        "Any staff member discovering an unresponsive, pulseless patient must immediately call for help, press the Code Blue wall button, and begin chest compressions. Team roles include: Code Team Leader (ICU Physician/Intensivist), Airway Specialist (Anesthesiologist/Respiratory Therapist), Compressor 1 & 2, Medication Nurse, Defibrillator Operator, and Recorder/Timer.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "4.0 Response Time Standards and Overhead Announcement",
                    "content": [
                        "The telecommunications operator must broadcast the Code Blue overhead public address announcement within 30 seconds of receiving the alert. The Rapid Response Team (RRT) and designated Code Blue team members must arrive on scene within 3 minutes of initial dispatch.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [105, 115, 120, 160],
                    "header": ["Code Designation", "Trigger Event", "Immediate Lead Team", "Response Time Standard"],
                    "rows": [
                        ["Code Blue (Adult)", "Cardiac or respiratory arrest", "RRT / ICU Code Blue Team", "on scene within 3 minutes"],
                        ["Code White (Pediatric)", "Pediatric arrest (< 18 yrs)", "PICU / PALS Resuscitation Team", "On scene within 3 minutes"],
                        ["Code Red (Fire)", "Smoke, heat, or active flame", "Facilities & Local Fire Marshall", "Immediate overhead (< 30s)"],
                        ["Code Pink", "Missing newborn or infant", "Security & All Unit Lockdown", "Lockdown doors within 60s"],
                        ["Code Silver", "Armed assailant with weapon", "Hospital Security & Police Dispatch", "Immediate run/hide/fight alert"],
                    ],
                },
            ],
            # Page 3
            [
                {
                    "type": "section",
                    "heading": "5.0 High-Quality Cardiopulmonary Resuscitation (CPR) Benchmarks",
                    "content": [
                        "Chest compressions must meet American Heart Association (AHA) high-quality CPR metrics: compression rate of 100 to 120 chest compressions per minute, compression depth of 2.0 to 2.4 inches (5 to 6 cm) for adults, complete chest recoil between compressions, and minimal interruptions (< 10 seconds). Compressors must rotate every 2 minutes.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "6.0 Defibrillation Protocol and Advanced Cardiac Life Support (ACLS)",
                    "content": [
                        "The defibrillator must be connected and the cardiac rhythm analyzed within 2 minutes of code team arrival. For shockable rhythms (Ventricular Fibrillation / Pulseless Ventricular Tachycardia), deliver an initial biphasic shock of 120 to 200 Joules, immediately resuming chest compressions without pausing for pulse check.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Arrest Rhythm", "Defibrillation Shock", "Primary Vasopressor", "Antiarrhythmic Agent"],
                    "rows": [
                        ["Ventricular Fibrillation (VF)", "Biphasic 120 - 200 J", "Epinephrine 1 mg IV q3-5m", "Amiodarone 300 mg bolus, then 150mg"],
                        ["Pulseless VT", "Biphasic 120 - 200 J", "Epinephrine 1 mg IV q3-5m", "Lidocaine 1 - 1.5 mg/kg alternative"],
                        ["Asystole", "No shock advised", "Epinephrine 1 mg IV q3-5m", "Identify & treat reversible causes (H/T)"],
                        ["PEA (Pulseless Electrical)", "No shock advised", "Epinephrine 1 mg IV q3-5m", "Treat underlying etiology immediately"],
                    ],
                },
            ],
            # Page 4
            [
                {
                    "type": "section",
                    "heading": "7.0 Airway Management and Capnography Targets",
                    "content": [
                        "Initial ventilation is provided using a bag-valve-mask with 100% oxygen at a ratio of 30 compressions to 2 ventilations. Upon endotracheal intubation, continuous waveform capnography must be utilized; end-tidal CO2 (PETCO2) values < 10 mmHg indicate inadequate compressions, while an abrupt rise in PETCO2 to > 35 mmHg indicates return of spontaneous circulation (ROSC).",
                    ],
                },
                {
                    "type": "section",
                    "heading": "8.0 Pediatric Resuscitation (Code White) Adaptations",
                    "content": [
                        "Code White designates pediatric medical emergencies (< 18 years). Resuscitation drug dosing must utilize length-based resuscitation tapes (Broselow tape). Epinephrine dosing is 0.01 mg/kg (0.1 mL/kg of 0.1 mg/mL formulation) IV/IO, and defibrillation begins at 2 Joules/kg.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [110, 115, 115, 160],
                    "header": ["Pediatric Parameter", "Broselow Zone Standard", "Resuscitation Guideline", "Monitoring Marker"],
                    "rows": [
                        ["Airway Sizing", "Internal diameter (Age/4) + 4", "Cuffed or uncuffed ET tube", "Continuous waveform capnography"],
                        ["Epinephrine Dosing", "0.01 mg/kg IV/IO (max 1 mg)", "Administer every 3 to 5 minutes", "Flush with 5 mL normal saline"],
                        ["Initial Defibrillation", "2 Joules / kg biphasic", "Subsequent shocks at 4 J/kg", "Immediate resumption of CPR"],
                        ["Fluid Resuscitation", "20 mL / kg Normal Saline bolus", "Over 10 to 20 minutes IV push", "Reassess liver edge and lung rales"],
                    ],
                },
            ],
            # Page 5
            [
                {
                    "type": "section",
                    "heading": "9.0 Emergency Crash Cart Maintenance and Lock Auditing",
                    "content": [
                        "Crash carts located in inpatient units, procedural suites, and clinics must be inspected daily by 08:00 AM by nursing staff. Verification includes checking the integrity of the numbered tamper-evident breakaway seal, defibrillator self-test pass, oxygen tank pressure (> 1000 psi), and suction canister function. Medication drawers expire every 30 days and are exchanged by the pharmacy.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "10.0 Code Red (Fire and Smoke) Procedure and Evacuation Tiers",
                    "content": [
                        "Code Red indicates fire or smoke detection. Staff must execute the RACE protocol: Rescue patients in immediate danger, Alarm (pull fire alarm box and call emergency operator), Contain (close all patient room doors and fire barrier doors), and Extinguish/Evacuate. Fire extinguishers must be operated using the PASS method (Pull, Aim, Squeeze, Sweep).",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Crash Cart Element", "Inspection Standard", "Verification Time", "Action if Non-Compliant"],
                    "rows": [
                        ["Tamper Seal Integrity", "Numbered seal intact and logged", "daily by 08:00 AM", "Open cart; full inventory check"],
                        ["Defibrillator Self-Test", "Passed indicator visible", "Daily morning test", "Biomedical engineering stat page"],
                        ["Oxygen Cylinder Pressure", "Gauge reads > 1000 psi", "Daily morning check", "Replace cylinder immediately"],
                        ["Pharmacy Med Tray Date", "Within 30-day expiration window", "Monthly pharmacy exchange", "Stat pharmacy tray exchange"],
                    ],
                },
            ],
            # Page 6
            [
                {
                    "type": "section",
                    "heading": "11.0 Resuscitation Flow-Sheet Documentation in EMR",
                    "content": [
                        "The designated recorder nurse must document all resuscitation events contemporaneously on the physical Code Blue flow-sheet. The detailed event log—including exact times of shocks, medication administrations, rhythm changes, and ROSC—must be entered into the EMR resuscitation record within 60 minutes post-event.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "12.0 Post-Resuscitation Debriefing, Quality Review, and Escalation",
                    "content": [
                        "Immediately following code resolution, the code leader must conduct a 5-minute multidisciplinary hot debrief. The completed Code Blue flow-sheet must be forwarded to the Resuscitation Committee within 24 hours. Resuscitation metrics (time to first compression, time to first shock, ROSC rate) are audited monthly.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Resuscitation Metric", "Institutional Benchmark", "Measurement Frequency", "Governance Body"],
                    "rows": [
                        ["Time to First Compression", "< 60 seconds from collapse", "Every Code Blue audit", "Resuscitation Committee"],
                        ["Time to First Shock (VF/VT)", "< 2 minutes from team arrival", "Monthly quality review", "Critical Care Quality Panel"],
                        ["Compression Fraction (CCF)", "≥ 80% active compressions", "Defibrillator telemetry download", "AHA Get With The Guidelines Group"],
                        ["EMR Resuscitation Entry", "within 60 minutes post-event", "Daily incident reconciliation", "Health Information Management"],
                    ],
                },
            ],
            # Page 7
            [
                {
                    "type": "section",
                    "heading": "13.0 Post-Cardiac Arrest Care and Targeted Temperature Management",
                    "content": [
                        "Comatose adult patients with ROSC after cardiac arrest must be evaluated for Targeted Temperature Management (TTM) maintaining a constant temperature between 32°C and 36°C for at least 24 hours to preserve neurological function. Emergent coronary angiography is indicated for STEMI.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "14.0 Institutional Governance and Resuscitation Committee Ratification",
                    "content": [
                        "This SOP is reviewed annually by the Resuscitation Committee and endorsed by the Chief Medical Officer.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [70, 85, 195, 150],
                    "header": ["Version", "Effective Date", "Summary of Revisions", "Approved Authority"],
                    "rows": [
                        ["v1.0", "2024-01-01", "Standardized hospital-wide emergency code response", "Emergency Preparedness Council"],
                        ["v2.0", "2025-01-01", "Integrated AHA 2025 CPR metrics and TTM protocols", "Resuscitation Committee"],
                        ["v3.0", "2026-01-01", "Mandated crash cart 08:00 inspection and 60m EMR entry", "Chief Medical Officer"],
                    ],
                },
            ],
        ],
    },
    "patient_identification": {
        "filename": "sop_patient_identification.pdf",
        "doc_id": "SOP-PID-2026-10",
        "department": "Patient Access & Clinical Quality",
        "subtitle": "METROPOLITAN HEALTH SYSTEM — PATIENT SAFETY GOALS",
        "title": "STANDARD OPERATING PROCEDURE: TWO-IDENTIFIER PATIENT IDENTIFICATION AND WRISTBAND STANDARDS",
        "effective_date": "2026-01-01",
        "review_cycle": "Annual",
        "pages": [
            # Page 1
            [
                {
                    "type": "section",
                    "heading": "1.0 Purpose and National Patient Safety Goals",
                    "content": [
                        "Misidentification of patients is a primary root cause of adverse drug events, surgical errors, transfusion reactions, and diagnostic delays. This SOP establishes hospital-wide standards for positive patient identification in compliance with Joint Commission National Patient Safety Goals.",
                        "Every staff member is personally responsible for verifying patient identity before rendering care, administering treatments, or transporting patients. Two-identifier verification must be an active, verbal, and visual process.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "2.0 Approved Patient Identifiers and Prohibited Proxies",
                    "content": [
                        "Clinical personnel must use at least two approved independent patient identifiers prior to any clinical encounter: (1) Patient full legal name and (2) Date of birth (DOB) or Medical Record Number (MRN). Room number and bed location are strictly prohibited as identifiers under any circumstances.",
                    ],
                },
            ],
            # Page 2
            [
                {
                    "type": "section",
                    "heading": "3.0 Wristband Issuance, Placement, and Barcode Printing",
                    "content": [
                        "A standardized thermal-printed barcoded identification wristband must be generated and applied to the patient's right wrist within 15 minutes of registration. The wristband must display: full legal name, date of birth, MRN, account number, attending physician, and high-resolution 2D barcode.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "4.0 Color-Coded Alert Wristband Conventions",
                    "content": [
                        "Standardized color-coded alert wristbands convey critical clinical warnings: Red indicates Allergy Alert; Yellow indicates Fall Risk; Purple indicates Do Not Resuscitate (DNR); Pink indicates Restricted Extremity (Limb Alert: no IV, blood pressure, or venipuncture on that arm).",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [85, 110, 145, 160],
                    "header": ["Band Color", "Clinical Alert Meaning", "Placement Threshold / Trigger", "Removal Authority"],
                    "rows": [
                        ["White (Standard)", "Primary Patient Identification", "Mandatory on all registered patients", "Upon formal discharge only"],
                        ["Red Alert", "Documented Drug / Food Allergy", "Any verified severe clinical allergy", "Pharmacist or RN verification"],
                        ["Yellow Alert", "Inpatient Fall Risk", "Morse Fall Scale score ≥ 51", "Nurse Manager post-discharge"],
                        ["Purple Alert", "Purple indicates Do Not Resuscitate (DNR)", "Valid signed DNR/POLST order in chart", "Attending Physician revocation"],
                        ["Pink Alert", "Limb Restriction / Mastectomy / AV Fistula", "No IV, BP cuff, or venipuncture on arm", "Vascular Surgeon / Charge RN"],
                    ],
                },
            ],
            # Page 3
            [
                {
                    "type": "section",
                    "heading": "5.0 Verification Moments Across the Care Continuum",
                    "content": [
                        "Active dual-identifier verification is mandatory before: (1) administering medications or vaccinations, (2) drawing blood or collecting specimens, (3) initiating blood product transfusions, (4) performing diagnostic imaging, (5) transporting patients between hospital units, and (6) initiating invasive procedures.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "6.0 Point-of-Care Barcode Scanning Protocol",
                    "content": [
                        "Bedside clinicians must scan the patient's wristband 2D barcode using the handheld barcode scanner before every medication administration or specimen collection. Clinical staff must scan the patient barcode prior to donning gloves for venipuncture or IV line access.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Clinical Touchpoint", "Primary Identification Method", "Secondary Verification Step", "Acceptable Exception"],
                    "rows": [
                        ["Medication Administration", "Barcode scanner read of band", "Compare with eMAR drug display", "Emergency ACLS resuscitation"],
                        ["Phlebotomy / Lab Draw", "Ask patient to state name & DOB", "Scan wristband barcode to print labels", "Unresponsive trauma patient"],
                        ["Blood Transfusion", "Dual-clinician verbal read-back", "Scan unit & patient band into eMAR", "No exception permitted"],
                        ["Diagnostic Radiology", "Verbal check + wristband inspect", "Reconcile with requisition order", "Trauma bay rapid X-ray protocol"],
                    ],
                },
            ],
            # Page 4
            [
                {
                    "type": "section",
                    "heading": "7.0 Patient Identification in Ambulatory and Outpatient Clinics",
                    "content": [
                        "In outpatient clinics where wristbands are not routinely worn, the clinic nurse or receptionist must actively ask the patient to state their full legal name and date of birth, comparing the verbal response directly against the electronic medical record schedule.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "8.0 Unidentified Patient / Trauma Protocol (Emergency Doe Naming)",
                    "content": [
                        "Unidentified trauma or comatose patients presenting to the Emergency Department must be assigned a standardized emergency alias (e.g., 'Trauma-Alpha, Male-01') and a temporary MRN. A barcoded wristband must be affixed immediately. Once true identity is verified by fingerprints or next of kin, health information management merges records within 24 hours.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [110, 115, 115, 160],
                    "header": ["Trauma Category", "Emergency Alias Template", "Temporary MRN Sequence", "Record Merge SLA"],
                    "rows": [
                        ["Unidentified Male Trauma", "Trauma-Alpha [Letter], Male [Number]", "Series 990-XXXXXX", "HIM merge within 24 hours"],
                        ["Unidentified Female Trauma", "Trauma-Beta [Letter], Female [Number]", "Series 991-XXXXXX", "HIM merge within 24 hours"],
                        ["Mass Casualty Incident (MCI)", "Disaster-Triage-[Color]-[Number]", "MCI Barcoded Tag Series", "Incident Command review"],
                        ["Found Confused / Wandering", "Doe-John / Doe-Jane [Serial ID]", "Series 992-XXXXXX", "Social Work / Police crossmatch"],
                    ],
                },
            ],
            # Page 5
            [
                {
                    "type": "section",
                    "heading": "9.0 Surgical Safety Checklist and Pre-Incision \"Time-Out\"",
                    "content": [
                        "Prior to the induction of anesthesia and again immediately before surgical skin incision, the operative team must conduct a formal 'Time-Out'. The circulating nurse, surgeon, and anesthesiologist must pause all activities and verbally confirm: correct patient identity, correct procedure, correct surgical site and marking, and relevant implants.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "10.0 Damaged, Defaced, or Missing Band Replacement Workflow",
                    "content": [
                        "If a patient wristband becomes soiled, illegible, torn, or removed for IV placement, the primary nurse must print a replacement band within 10 minutes. Two licensed healthcare workers must re-verify the patient identity using verbal confirmation and medical record comparison prior to affixing the new band.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Discrepancy Event", "Immediate Clinical Action", "Replacement Timeframe", "Sign-Off Requirement"],
                    "rows": [
                        ["Damaged / Torn Band", "Reprint barcoded wristband", "within 10 minutes", "Dual-nurse physical verify"],
                        ["Band Cut for IV Placement", "Affix replacement to opposite limb", "Prior to initiating IV cannula", "Document in EMR nursing note"],
                        ["Name Spelling Mismatch", "Halt non-emergent medication passes", "Patient Access reprint in 15m", "Registration Supervisor audit"],
                        ["Missing Barcode Band", "Stop all procedural care", "Stat print and bedside check", "Charge Nurse co-signature"],
                    ],
                },
            ],
            # Page 6
            [
                {
                    "type": "section",
                    "heading": "11.0 EMR Audit Trails and Verification Logging",
                    "content": [
                        "All barcode scans and manual patient identification overrides are logged automatically in the EMR audit trail. The Hospital Quality Department monitors barcode scanning compliance monthly with an institutional target of ≥ 98% barcode verification for all medication and blood administrations.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "12.0 Near-Miss Reporting, Safety Review, and Incident Escalation",
                    "content": [
                        "Any wrong-patient near-miss, wrong-band placement, or specimen labeling discrepancy must be entered into the hospital incident reporting system immediately. The clinical charge nurse must escalate the near-miss to the Risk Manager within 2 hours of discovery for immediate safety investigation.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Near-Miss Severity", "Clinical Occurrence", "Escalation Deadline", "Investigative Action"],
                    "rows": [
                        ["Level 1 Discrepancy", "Wrong band printed; caught before placement", "Log in portal by shift end", "Registration quality coaching"],
                        ["Level 2 Near-Miss", "Wrong patient scanned; BCMA alert stopped dose", "Log within 4 hours", "Unit practice committee review"],
                        ["Level 3 Safety Breach", "Wrong-patient blood draw or medication given", "within 2 hours to Risk Manager", "Comprehensive root cause review"],
                        ["Sentinel Event", "Wrong patient surgery or fatal mismatched unit", "Immediate executive escalation", "RCA within 30 days & Board report"],
                    ],
                },
            ],
            # Page 7
            [
                {
                    "type": "section",
                    "heading": "13.0 Newborn and Pediatric Identification Standards",
                    "content": [
                        "Newborns delivered in the hospital must receive two matching barcoded identification bands (one on the wrist, one on the ankle) within 5 minutes of birth. Matching bands with identical four-part numbering must be placed on the mother and her designated support partner.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "14.0 Institutional Governance and Patient Access Ratification",
                    "content": [
                        "This SOP is reviewed annually by the Patient Safety Committee and approved by the Chief Medical Officer.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [70, 85, 195, 150],
                    "header": ["Version", "Effective Date", "Summary of Revisions", "Approved Authority"],
                    "rows": [
                        ["v1.0", "2024-01-01", "Initial positive patient identification standard", "Patient Access Governance"],
                        ["v2.0", "2025-01-01", "Standardized color-coded wristbands and barcode targets", "Patient Safety Committee"],
                        ["v3.0", "2026-01-01", "Enforced 10m band replacement and 2h risk escalation", "Chief Medical Officer"],
                    ],
                },
            ],
        ],
    },
    "biomedical_waste": {
        "filename": "sop_biomedical_waste.pdf",
        "doc_id": "SOP-WASTE-2026-11",
        "department": "Environmental Health & Safety & Facilities Management",
        "subtitle": "METROPOLITAN HEALTH SYSTEM — ENVIRONMENTAL SAFETY POLICY",
        "title": "STANDARD OPERATING PROCEDURE: BIOMEDICAL AND HAZARDOUS WASTE SEGREGATION AND DISPOSAL",
        "effective_date": "2026-01-01",
        "review_cycle": "Annual",
        "pages": [
            # Page 1
            [
                {
                    "type": "section",
                    "heading": "1.0 Purpose and Environmental Protection Mandates",
                    "content": [
                        "Improper disposal of biomedical and hazardous waste presents severe public health, occupational, and environmental risks. This standard operating procedure governs the segregation, containment, transport, storage, and disposal of regulated medical waste in compliance with OSHA, EPA, and DOT regulations.",
                        "Strict segregation at the point of origin minimizes environmental pollution, ensures occupational safety for clinical and sanitation personnel, and prevents regulatory fines associated with contaminated waste streams.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "2.0 Regulatory Framework (OSHA, EPA, DOT)",
                    "content": [
                        "All hospital facilities must comply with OSHA Bloodborne Pathogens Standard (29 CFR 1910.1030), EPA Resource Conservation and Recovery Act (RCRA), and DOT Hazardous Materials Regulations (49 CFR 173). Environmental services staff handling biohazard waste must undergo certified annual training.",
                    ],
                },
            ],
            # Page 2
            [
                {
                    "type": "section",
                    "heading": "3.0 Biohazard Waste Stream Classification",
                    "content": [
                        "Hospital waste is classified into distinct categories: general solid waste (non-hazardous), regulated medical waste (biohazard/infectious), pathological waste, chemotherapy trace waste, hazardous chemical waste, and radioactive waste. Mixing regulated biomedical waste into general municipal trash is strictly prohibited.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "4.0 Color-Coded Receptacle and Bagging Standards",
                    "content": [
                        "Waste must be segregated at the point of origin into color-coded containers: Red bags/bins for regulated infectious waste (blood-soaked gauze, saturated dressings, IV tubing with blood); Yellow containers for pathological and anatomical waste; Blue bins for contaminated glassware and ampoules; Black containers for hazardous chemical and bulk chemotherapy waste.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [90, 110, 140, 160],
                    "header": ["Waste Stream", "Container / Bag Color", "Exemplar Clinical Items", "Approved Final Treatment"],
                    "rows": [
                        ["Regulated Medical", "Red Biohazard Bag", "Saturated gauze, bloody tubing, suction cans", "Autoclave shredding / thermal treatment"],
                        ["Pathological Waste", "Yellow Rigid Container", "Biopsy specimens, amputated tissue, organs", "High-temperature incineration"],
                        ["Sharps Waste", "White Translucent Box", "Needles, scalpels, glass ampoules, trocars", "Puncture-proof seal & autoclave/incinerate"],
                        ["Trace Chemotherapy", "Yellow Sharps / Box", "Empty chemo vials, IV bags (< 3% residual)", "Incineration at licensed RCRA facility"],
                        ["Hazardous Chemical", "Black RCRA Container", "Bulk antineoplastics, expired toxic drugs", "Licensed hazardous waste destruction"],
                    ],
                },
            ],
            # Page 3
            [
                {
                    "type": "section",
                    "heading": "5.0 Sharps Management and Container Fill Limits",
                    "content": [
                        "All needles, scalpel blades, lancets, glass ampoules, and trocars must be discarded immediately into rigid, puncture-resistant, leak-proof sharps containers. Sharps containers must be sealed and replaced when 3/4 full; overfilling or manually pushing sharps into containers is strictly prohibited.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "6.0 Pathological and Chemotherapy Trace Waste Handover",
                    "content": [
                        "Pathological waste (tissue biopsies, human organs, amputated limbs) must be placed in yellow rigid containers labeled 'BIOHAZARD - PATHOLOGICAL WASTE' and frozen at < -10°C pending incineration. Trace chemotherapy waste (vials, syringes with < 3% residual volume) must be discarded in yellow chemotherapy sharps bins.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Sharps Category", "Receptacle Type", "Handling Protocol", "Fill Capacity Standard"],
                    "rows": [
                        ["Contaminated Needles", "Wall-mounted sharps unit", "Safety-engineered retractable needle", "when 3/4 full"],
                        ["Surgical Scalpel Blades", "OR magnetic sharps counter", "Never recap by hand; use mechanical pass", "Lock container at case end"],
                        ["Glass Ampoules / Vials", "Puncture-proof sharps box", "Discard directly; no pre-washing", "when 3/4 full"],
                        ["Chemotherapy Needles", "Dedicated yellow sharps unit", "Aerosol-sealed disposal slot", "Seal when 3/4 full"],
                    ],
                },
            ],
            # Page 4
            [
                {
                    "type": "section",
                    "heading": "7.0 Central Holding Area Storage Times and Temperature Controls",
                    "content": [
                        "Regulated medical waste must be transported from unit utility rooms to the hospital Central Biohazard Storage Holding Area. Unrefrigerated biohazard waste stored in central holding room is 48 hours maximum. If storage exceeds 48 hours, waste must be kept in a refrigerated holding room at < 4°C (39°F) for no longer than 7 days.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "8.0 PPE Requirements: Heavy-Duty Utility Glove Standards",
                    "content": [
                        "Environmental services personnel handling regulated medical waste bags or transporting biohazard carts must wear personal protective equipment: Heavy-duty 14-mil nitrile utility gloves, puncture-resistant safety boots with steel toes, fluid-resistant coveralls, and full-face splash shields. Standard thin examination gloves are strictly prohibited for bulk waste transport.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Personnel Role", "Glove Specification", "Body Barrier Protection", "Footwear & Eye Protection"],
                    "rows": [
                        ["Waste Cart Collector", "Heavy-duty 14-mil nitrile utility gloves", "AAMI Level 3 fluid-proof coverall", "Steel-toe puncture boots & goggles"],
                        ["Holding Room Operator", "Heavy-duty 14-mil nitrile utility gloves", "Heavy rubber apron over jumpsuit", "Safety boots & full face shield"],
                        ["Unit EVS Cleaner", "Heavy-duty 11-mil nitrile gloves", "Water-resistant isolation gown", "Slip-resistant closed toe shoes"],
                        ["Sharps Box Exchanger", "Cut-resistant Level 4 Kevlar/Nitrile", "Fluid-resistant lab coat", "Protective safety spectacles"],
                    ],
                },
            ],
            # Page 5
            [
                {
                    "type": "section",
                    "heading": "9.0 Chemical and Biohazard Spill Response Kit Deployment",
                    "content": [
                        "Biohazard spill kits must be stationed on every clinical unit. Spills of blood or bodily fluid > 50 mL require immediate cordon, notification of Environmental Services, and dispatch of a spill cleanup team within 10 minutes. Decontamination requires applying 1% sodium hypochlorite (10,000 ppm available chlorine) with a mandatory contact time of 30 minutes before absorbing.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "10.0 Occupational Exposure Protocol (Sharps & Splashes)",
                    "content": [
                        "Any employee who sustains a contaminated needle-stick injury or mucous membrane splash must wash the site immediately with soap and water for 15 minutes. The employee must report immediately to Occupational Health or the Emergency Department for PEP within 2 hours of exposure to initiate post-exposure prophylaxis.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [105, 120, 115, 160],
                    "header": ["Spill Magnitude", "First Responder Action", "Chemical Decontaminant", "Contact Dwell Time"],
                    "rows": [
                        ["Small Spot (< 10 mL)", "Wipe with disinfectant wipe", "0.5% Sodium hypochlorite wipe", "4 minutes wet contact"],
                        ["Medium Spill (10-50 mL)", "Absorbent powder + wipe", "1:10 Bleach dilution (5,000 ppm)", "10 minutes wet contact"],
                        ["Large Gross Spill (> 50 mL)", "Dispatch team in 10 minutes", "1% Sodium hypochlorite (10,000 ppm)", "30 minutes contact time"],
                        ["Chemotherapy Spill", "Deploy specialized HD spill kit", "Bleach neutralizer + thiosulfate", "20 minutes neutralizing soak"],
                    ],
                },
            ],
            # Page 6
            [
                {
                    "type": "section",
                    "heading": "11.0 Electronic Waste Tracking and Manifest Documentation",
                    "content": [
                        "All biohazard waste consignments leaving the facility must be accompanied by a state-compliant Hazardous Waste Manifest. Waste manifests must record container barcodes, net weight in kilograms, licensed carrier certification, and treatment facility destination. Manifest records must be retained for 5 years.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "12.0 Environmental Compliance Audits and Penalty Escalation",
                    "content": [
                        "Weekly environmental safety audits inspect unit segregation compliance. Any improper segregation incident (e.g., sharps found in regular trash) triggers a level-one violation report. Persistent non-compliance within a department escalates to the Director of Facilities and Safety Committee within 24 hours.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Compliance Check", "Acceptable Standard", "Audit Cadence", "Escalation Authority"],
                    "rows": [
                        ["Sharps Fill Compliance", "100% containers ≤ 3/4 capacity", "Weekly unit safety inspection", "Unit Nurse Manager"],
                        ["Red Bag Segregation Error", "Zero non-infectious municipal trash", "Monthly random bin audit", "EVS Operations Supervisor"],
                        ["Storage Time Limit", "≤ 48 hours unrefrigerated", "Daily holding log review", "Safety Officer in 24 hours"],
                        ["Manifest Archival SLA", "100% manifest logs complete", "Quarterly EPA audit prep", "Environmental Health Director"],
                    ],
                },
            ],
            # Page 7
            [
                {
                    "type": "section",
                    "heading": "13.0 Pharmaceutical Waste Disposal and Sink Disposal Ban",
                    "content": [
                        "Disposal of pharmaceuticals by flushing down toilets or hospital sinks is strictly prohibited by EPA regulations. Expired, wasted, or partial vials of non-controlled medications must be placed in designated pharmaceutical waste containers for reverse distributor return or thermal destruction.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "14.0 Institutional Governance and Safety Committee Ratification",
                    "content": [
                        "This SOP is reviewed annually by the Environmental Health and Safety Committee and approved by the Chief Operating Officer.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [70, 85, 195, 150],
                    "header": ["Version", "Effective Date", "Summary of Revisions", "Approved Authority"],
                    "rows": [
                        ["v1.0", "2024-01-01", "Initial environmental biomedical waste standard", "EHS Steering Committee"],
                        ["v2.0", "2025-01-01", "Standardized RCRA black box and EPA pharmaceutical rules", "Facilities Governance Board"],
                        ["v3.0", "2026-01-01", "Mandated 14-mil utility gloves and 5-year manifest retention", "Chief Operating Officer"],
                    ],
                },
            ],
        ],
    },
    "pharmacy_storage": {
        "filename": "sop_pharmacy_storage.pdf",
        "doc_id": "SOP-PHAR-2026-12",
        "department": "Department of Pharmacy Services",
        "subtitle": "METROPOLITAN HEALTH SYSTEM — PHARMACY ADMINISTRATIVE POLICY",
        "title": "STANDARD OPERATING PROCEDURE: PHARMACEUTICAL COLD CHAIN MANAGEMENT AND INVENTORY STORAGE",
        "effective_date": "2026-01-01",
        "review_cycle": "Annual",
        "pages": [
            # Page 1
            [
                {
                    "type": "section",
                    "heading": "1.0 Purpose and USP General Chapters (<659>, <797>, <800>)",
                    "content": [
                        "Proper storage of pharmaceuticals is vital to preserve drug potency, prevent chemical degradation, and ensure patient safety. This standard operating procedure enforces temperature specifications, cold chain monitoring, security controls, and inventory auditing across all pharmacy storage areas in accordance with USP <659>, <797>, and <800>.",
                        "Maintaining uninterrupted cold chain conditions is essential for vaccines, biological therapeutics, insulins, and blood clotting factors. Failure of climate control compromises clinical efficacy and requires immediate quarantine of affected stock.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "2.0 Standard Temperature Range Specifications",
                    "content": [
                        "All pharmaceutical storage locations must adhere strictly to USP temperature standards: Refrigerated cold storage must be maintained between 2°C to 8°C (36°F to 46°F); Freezer storage must be maintained between -25°C to -10°C (-13°F to 14°F); Controlled Room Temperature (CRT) must be maintained between 20°C to 25°C (68°F to 77°F) with excursions permitted between 15°C to 30°C.",
                    ],
                },
            ],
            # Page 2
            [
                {
                    "type": "section",
                    "heading": "3.0 Continuous Monitoring and NIST Data Logger Calibration",
                    "content": [
                        "All medication refrigerators and freezers must be equipped with continuous automated temperature monitoring systems utilizing NIST-traceable calibrated digital data loggers. Sensors must record temperatures every 15 minutes with high/low readings uploaded to the pharmacy server.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "4.0 Twice-Daily Manual Verification and Documentation",
                    "content": [
                        "In addition to automated electronic logging, a designated pharmacy technician must physically inspect digital thermometer displays and document temperatures twice daily (by 09:00 AM and 17:00 PM). Documentation must be recorded in the pharmacy EMR temperature tracking log with staff initials.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Storage Zone", "Target Temp Celsius", "Target Temp Fahrenheit", "Sensor Alert Tolerance"],
                    "rows": [
                        ["Refrigerated Storage", "2°C to 8°C (36°F to 46°F)", "36°F to 46°F", "Alert if < 2°C or > 8°C for 15m"],
                        ["Freezer Storage", "-25°C to -10°C", "-13°F to 14°F", "Alert if > -10°C for 20m"],
                        ["Controlled Room Temp", "20°C to 25°C", "68°F to 77°F", "Alert if < 18°C or > 26°C for 60m"],
                        ["Ultra-Low Vaccine Freezer", "-80°C to -60°C", "-112°F to -76°F", "Alert if > -60°C for 10m"],
                    ],
                },
            ],
            # Page 3
            [
                {
                    "type": "section",
                    "heading": "5.0 Cold Chain Excursion Thresholds and Alarm Systems",
                    "content": [
                        "Automated monitoring systems trigger audio-visual alarms and broadcast SMS alerts to the On-Call Pharmacist when temperatures breach limits for > 15 minutes. An excursion outside 2°C to 8°C lasting > 30 minutes requires immediate physical inspection of unit seals, compressor status, and door latching.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "6.0 Quarantine Protocols for Suspect or Temperature-Exposed Stock",
                    "content": [
                        "Medications exposed to an out-of-range temperature excursion must be removed immediately and placed into an insulated Yellow quarantine tote labeled 'QUARANTINE - DO NOT DISPENSE'. The clinical specialist must contact manufacturers within 4 hours to obtain stability data before release or destruction.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [105, 120, 115, 160],
                    "header": ["Excursion Window", "Notification Severity", "Responding Personnel", "Mandatory Action"],
                    "rows": [
                        ["1 to 15 minutes", "Yellow Warning Alert", "Area Lead Technician", "Verify door closure and probe position"],
                        ["16 to 30 minutes", "Orange Escalation Alert", "Staff Pharmacist on Duty", "Inspect secondary sensor and compressor"],
                        ["> 30 minutes excursion", "Red High-Priority Alert", "Lead Pharmacist & Facilities", "Move stock to Yellow quarantine tote"],
                        ["> 120 minutes out-of-spec", "Critical Equipment Failure", "Director of Pharmacy Services", "Transfer all stock to backup refrigerators"],
                    ],
                },
            ],
            # Page 4
            [
                {
                    "type": "section",
                    "heading": "7.0 Controlled Substance Secure Storage (Schedule II-V)",
                    "content": [
                        "Schedule II controlled substances (opioids, amphetamines) must be secured in a Class 5 dual-locked safe or vault equipped with dual-biometric sign-on and continuous video surveillance. Access is restricted to licensed pharmacists. Perpetual electronic inventory must be counted every 24 hours with dual-pharmacist verification.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "8.0 Hazardous Drug and Chemotherapy Cold Storage",
                    "content": [
                        "Hazardous antineoplastic medications requiring refrigeration must be stored in dedicated negative-pressure cleanrooms or dedicated chemo-refrigerators exhausting directly to the outside. Pharmacists handling cytotoxic vials must wear powder-free chemo-tested nitrile gloves meeting ASTM D6978.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Drug Schedule", "Storage Enclosure", "Access Credentials", "Physical Audit Cadence"],
                    "rows": [
                        ["Schedule II (C-II)", "Class 5 Dual-Locked Vault", "Dual-Biometric + Key Card", "counted every 24 hours"],
                        ["Schedule III - V (C-III-V)", "Locked Steel Vault Compartment", "Single Biometric Pharmacist Login", "Weekly perpetual count"],
                        ["Refrigerated Chemo", "Negative-Pressure Biological Box", "Chemo-certified Pharmacist only", "Monthly lot and expiration check"],
                        ["Floor Stock ADC C-II", "Individual Locking Matrix Drawer", "Dual RN Witness Fingerprint Scan", "Every shift change count"],
                    ],
                },
            ],
            # Page 5
            [
                {
                    "type": "section",
                    "heading": "9.0 Vaccine Storage and Handling Guidelines (CDC VFC)",
                    "content": [
                        "Vaccine storage must comply with CDC Vaccines for Children (VFC) guidelines. Dormitory-style compact refrigerators with combined freezer compartments are strictly prohibited. Vaccines must be stored in central wire baskets away from refrigerator walls, coils, and door shelves. Water bottles must line door shelves to stabilize temperatures.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "10.0 Expired, Recalled, and Damaged Inventory Removal",
                    "content": [
                        "Pharmacy inventory audits are conducted monthly on the 1st business day of each month. All pharmaceuticals with expiration dates within the upcoming 30 days must be pulled from active dispensing shelves and transferred to the reverse distribution holding area.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Inventory Category", "Inspection Schedule", "Removal Cutoff", "Disposal Route"],
                    "rows": [
                        ["Routine Active Stock", "Monthly on 1st business day", "Expires in < 30 days", "Transfer to reverse distributor"],
                        ["Vaccine Inventory", "Weekly on Monday morning", "Expires within current month", "CDC VFC return process"],
                        ["Compounded Sterile Prep", "Daily at start of shift", "Beyond-Use Date (BUD) reached", "Hazardous pharmaceutical waste bin"],
                        ["Recalled Products (FDA)", "Immediate upon notification", "Within 2 hours of FDA alert", "Quarantine in secure holding cage"],
                    ],
                },
            ],
            # Page 6
            [
                {
                    "type": "section",
                    "heading": "11.0 Backup Power and Emergency Transfer Protocols",
                    "content": [
                        "All pharmacy refrigerators, freezers, and cleanrooms must be connected to emergency red generator power outlets capable of activating within 10 seconds of municipal power loss. If generator failure occurs, staff must transfer cold chain inventory into validated insulated transport coolers within 60 minutes.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "12.0 Pharmacy Quality Auditing, Loss Reporting, and Escalation",
                    "content": [
                        "The Director of Pharmacy conducts monthly audits of temperature logs, controlled substance discrepancies, and excursion incidents. Any cold storage failure resulting in potential medication spoilage or product loss exceeding $10,000 must be reported to the Chief Operating Officer within 2 hours.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [115, 110, 115, 160],
                    "header": ["Quality Indicator", "Audit Standard", "Audit Cadence", "Escalation Lead"],
                    "rows": [
                        ["Cold Chain Temperature Log", "100% twice-daily entries complete", "Monthly review", "Quality Safety Specialist"],
                        ["Controlled Substance Discrepancy", "Zero unexplained variance", "Immediate shift audit", "State Board of Pharmacy & DEA (24h)"],
                        ["Cold Storage Catastrophe", "product loss exceeding $10,000", "Incident basis (within 2h)", "Chief Operating Officer"],
                        ["Cleanroom Particle Counts", "ISO Class 7 and 8 specifications", "Semi-annual certification", "Cleanroom Engineering Director"],
                    ],
                },
            ],
            # Page 7
            [
                {
                    "type": "section",
                    "heading": "13.0 Automated Dispensing Cabinet (ADC) Floor Stock Storage",
                    "content": [
                        "Inpatient ADC units (Pyxis/Omnicell) located on clinical floors are restricted to controlled room temperature. Daily ADC temperature probes are monitored centrally by pharmacy automation engineers. Ambient temperature excursions > 25°C trigger immediate HVAC work orders.",
                    ],
                },
                {
                    "type": "section",
                    "heading": "14.0 Institutional Governance and Pharmacy & Therapeutics Endorsement",
                    "content": [
                        "This SOP is reviewed annually by the Pharmacy Operations Committee and approved by the Pharmacy and Therapeutics (P&T) Committee.",
                    ],
                },
                {
                    "type": "table",
                    "col_widths": [70, 85, 195, 150],
                    "header": ["Version", "Effective Date", "Summary of Revisions", "Approved Authority"],
                    "rows": [
                        ["v1.0", "2024-01-01", "Initial pharmacy cold chain storage standard", "P&T Committee"],
                        ["v2.0", "2025-01-01", "Implemented NIST digital monitoring and USP <800>", "Pharmacy Operations Panel"],
                        ["v3.0", "2026-01-01", "Enforced twice-daily check, 24h C-II count, and loss escalation", "Chief Operating Officer"],
                    ],
                },
            ],
        ],
    },
}

# ============================================================================
# EVALUATION QUESTIONS FOR SOPS (48 questions, 4 per SOP)
# ============================================================================

SOP_QUESTIONS: List[Dict[str, str]] = [
    # SOP 1: Infection Control
    {
        "id": "q_inf_01",
        "question": "What is the minimum number of air changes per hour mandated for an airborne infection isolation room?",
        "expected_doc": "sop_infection_control.pdf",
        "expected_section": "6.0 Airborne Infection Isolation Room (AIIR) Specifications",
        "expected_answer_snippet": "≥12 air changes per hour",
    },
    {
        "id": "q_inf_02",
        "question": "How long must bleach disinfectant solution remain wet on surfaces during terminal decontamination?",
        "expected_doc": "sop_infection_control.pdf",
        "expected_section": "7.0 Environmental Decontamination & Disinfection Timelines",
        "expected_answer_snippet": "10 minutes for bleach",
    },
    {
        "id": "q_inf_03",
        "question": "Within what timeframe must an outbreak cluster of two nosocomial infections be reported to the Chief Medical Officer?",
        "expected_doc": "sop_infection_control.pdf",
        "expected_section": "12.0 Clinical Governance, Audit, and Breach Escalation",
        "expected_answer_snippet": "within 4 hours",
    },
    {
        "id": "q_inf_04",
        "question": "What specific glove standard is required for standard examination barrier precautions?",
        "expected_doc": "sop_infection_control.pdf",
        "expected_section": "4.0 Personal Protective Equipment: Gloves, Gowns, and Respirators",
        "expected_answer_snippet": "ASTM D6319",
    },
    # SOP 2: Discharge Process
    {
        "id": "q_dis_01",
        "question": "What is the daily target cutoff time for patient departures from inpatient beds?",
        "expected_doc": "sop_discharge_process.pdf",
        "expected_section": "1.0 Objective and Target Departure Timelines",
        "expected_answer_snippet": "11:00 AM",
    },
    {
        "id": "q_dis_02",
        "question": "How soon after discharge must the attending physician finalize and sign the discharge summary?",
        "expected_doc": "sop_discharge_process.pdf",
        "expected_section": "3.0 Attending Physician Clinical Sign-Off Requirements",
        "expected_answer_snippet": "within 24 hours",
    },
    {
        "id": "q_dis_03",
        "question": "What LACE score threshold mandates a telephone wellness check within 48 to 72 hours?",
        "expected_doc": "sop_discharge_process.pdf",
        "expected_section": "10.0 Post-Discharge Telephonic Follow-Up (LACE Criteria)",
        "expected_answer_snippet": "LACE score ≥ 10",
    },
    {
        "id": "q_dis_04",
        "question": "Who is notified when a discharge is stalled more than 180 minutes past scheduled release?",
        "expected_doc": "sop_discharge_process.pdf",
        "expected_section": "12.0 Quality Metrics, Readmission Audit, and Delay Escalation",
        "expected_answer_snippet": "Inpatient Bed Management Director",
    },
    # SOP 3: Billing & Financial
    {
        "id": "q_bil_01",
        "question": "What is the maximum allowable window for departments to record clinical charges after care is provided?",
        "expected_doc": "sop_billing_financial.pdf",
        "expected_section": "3.0 Point-of-Care Charge Capture & Timelines",
        "expected_answer_snippet": "within 24 hours of service",
    },
    {
        "id": "q_bil_02",
        "question": "What income threshold relative to the Federal Poverty Level qualifies an uninsured patient for a complete write-off?",
        "expected_doc": "sop_billing_financial.pdf",
        "expected_section": "7.0 Financial Assistance Policy (FAP) and Poverty Guidelines",
        "expected_answer_snippet": "≤ 250% of the Federal Poverty Level",
    },
    {
        "id": "q_bil_03",
        "question": "To whom must disputed patient bills greater than 5000 dollars be escalated?",
        "expected_doc": "sop_billing_financial.pdf",
        "expected_section": "10.0 Dispute Resolution and Charge Grievance Process",
        "expected_answer_snippet": "Director of Revenue Cycle",
    },
    {
        "id": "q_bil_04",
        "question": "What is the hospital target percentage for first-pass clean insurance claims?",
        "expected_doc": "sop_billing_financial.pdf",
        "expected_section": "1.0 Purpose and Revenue Cycle Integrity",
        "expected_answer_snippet": "clean claim rate target is ≥ 96%",
    },
    # SOP 4: Medication Safety
    {
        "id": "q_med_01",
        "question": "What is the highest permitted continuous regular insulin infusion rate before requiring specialist authorization?",
        "expected_doc": "sop_medication_safety.pdf",
        "expected_section": "6.0 Intravenous Insulin Protocol and Glycemic Monitoring",
        "expected_answer_snippet": "10 units/hour",
    },
    {
        "id": "q_med_02",
        "question": "What is the expected therapeutic aPTT target window for patients on unfractionated heparin infusions?",
        "expected_doc": "sop_medication_safety.pdf",
        "expected_section": "7.0 Anticoagulation Management: Heparin and Low Molecular Weight Heparin",
        "expected_answer_snippet": "60 to 85 seconds",
    },
    {
        "id": "q_med_03",
        "question": "What type of gloves must healthcare staff put on when manipulating hazardous antineoplastic medications?",
        "expected_doc": "sop_medication_safety.pdf",
        "expected_section": "9.0 Personal Protective Equipment: Chemotherapy Glove Handling",
        "expected_answer_snippet": "ASTM D6978",
    },
    {
        "id": "q_med_04",
        "question": "Within what time frame must a medication error causing harm be reported to the Patient Safety Officer?",
        "expected_doc": "sop_medication_safety.pdf",
        "expected_section": "12.0 Adverse Drug Event Reporting and Root Cause Analysis Escalation",
        "expected_answer_snippet": "within 60 minutes",
    },
    # SOP 5: Patient Consent
    {
        "id": "q_con_01",
        "question": "For how many days is a signed informed consent form considered valid before an elective operation?",
        "expected_doc": "sop_patient_consent.pdf",
        "expected_section": "5.0 Validity Period and Re-Verification Before Surgery",
        "expected_answer_snippet": "maximum of 30 days",
    },
    {
        "id": "q_con_02",
        "question": "If a patient lacks decision-making capacity and has no legal guardian or proxy, who is next in line to make decisions?",
        "expected_doc": "sop_patient_consent.pdf",
        "expected_section": "6.0 Surrogate Decision-Maker Priority Order",
        "expected_answer_snippet": "Legal spouse",
    },
    {
        "id": "q_con_03",
        "question": "How quickly must an Ethics Committee review be arranged if surrogate decision makers are deadlocked?",
        "expected_doc": "sop_patient_consent.pdf",
        "expected_section": "12.0 Ethical Disputes, Refusals, and Legal Risk Escalation",
        "expected_answer_snippet": "within 6 hours",
    },
    {
        "id": "q_con_04",
        "question": "What time threshold justifies emergency intervention without prior consent to preserve life or limb?",
        "expected_doc": "sop_patient_consent.pdf",
        "expected_section": "8.0 Emergency Treatment Exception Protocol",
        "expected_answer_snippet": "within 15 minutes",
    },
    # SOP 6: Hand Hygiene
    {
        "id": "q_hyg_01",
        "question": "What is the recommended volume of alcohol rub to apply when sanitizing hands between patient contacts?",
        "expected_doc": "sop_hand_hygiene.pdf",
        "expected_section": "4.0 Alcohol-Based Hand Rub (ABHR) Technique and Volume",
        "expected_answer_snippet": "3 to 5 mL",
    },
    {
        "id": "q_hyg_02",
        "question": "How long should staff scrub with soap and water when managing spore-forming pathogens like C. diff?",
        "expected_doc": "sop_hand_hygiene.pdf",
        "expected_section": "5.0 Handwashing with Antimicrobial Soap and Running Water",
        "expected_answer_snippet": "40 to 60 seconds",
    },
    {
        "id": "q_hyg_03",
        "question": "What is the maximum allowed length of natural fingernails for healthcare providers offering direct patient care?",
        "expected_doc": "sop_hand_hygiene.pdf",
        "expected_section": "8.0 Fingernail Standards, Jewelry, and Skin Integrity Guidelines",
        "expected_answer_snippet": "0.25 inches (6 mm)",
    },
    {
        "id": "q_hyg_04",
        "question": "What performance percentage triggers escalation to the Chief Nursing Officer if a unit underperforms across two audit cycles?",
        "expected_doc": "sop_hand_hygiene.pdf",
        "expected_section": "12.0 Corrective Action Plans and Leadership Escalation",
        "expected_answer_snippet": "scoring < 85% compliance",
    },
    # SOP 7: Fall Prevention
    {
        "id": "q_fal_01",
        "question": "What Morse Fall Scale score marks a patient as being at high risk for falling?",
        "expected_doc": "sop_fall_prevention.pdf",
        "expected_section": "3.0 Morse Fall Scale (MFS) Scoring Methodology",
        "expected_answer_snippet": "High risk (≥ 51)",
    },
    {
        "id": "q_fal_02",
        "question": "How quickly must a non-contrast head CT scan be performed for a fallen patient on anticoagulation therapy?",
        "expected_doc": "sop_fall_prevention.pdf",
        "expected_section": "10.0 Post-Fall Neurological Checks and Emergency Head Imaging",
        "expected_answer_snippet": "within 60 minutes",
    },
    {
        "id": "q_fal_03",
        "question": "What visual identifiers must be placed on patients designated as high fall risk?",
        "expected_doc": "sop_fall_prevention.pdf",
        "expected_section": "6.0 Targeted Interventions for Moderate and High-Risk Patients",
        "expected_answer_snippet": "Yellow alert wristband, yellow non-skid socks",
    },
    {
        "id": "q_fal_04",
        "question": "Within what time limit must a formal incident report be submitted following a patient fall?",
        "expected_doc": "sop_fall_prevention.pdf",
        "expected_section": "11.0 Incident Documentation in EMR and Safety Portals",
        "expected_answer_snippet": "within 12 hours",
    },
    # SOP 8: Blood Transfusion
    {
        "id": "q_bld_01",
        "question": "How long is a patient blood type and screen specimen valid before requiring a redraw?",
        "expected_doc": "sop_blood_transfusion.pdf",
        "expected_section": "2.0 Pre-Transfusion Testing and Sample Validity",
        "expected_answer_snippet": "maximum 72 hours",
    },
    {
        "id": "q_bld_02",
        "question": "What is the maximum time allowed for a packed red blood cell unit to finish infusing once started?",
        "expected_doc": "sop_blood_transfusion.pdf",
        "expected_section": "6.0 Rate of Administration and 15-Minute Observation Rule",
        "expected_answer_snippet": "complete within 4 hours",
    },
    {
        "id": "q_bld_03",
        "question": "What degree of temperature elevation during transfusion is considered a clinical trigger for stopping the unit?",
        "expected_doc": "sop_blood_transfusion.pdf",
        "expected_section": "8.0 Recognition of Acute Transfusion Reactions (AHTR, TRALI, TACO)",
        "expected_answer_snippet": "increase ≥ 1.0°C (1.8°F)",
    },
    {
        "id": "q_bld_04",
        "question": "How quickly must suspected acute hemolytic reactions be escalated to the Blood Bank Medical Director?",
        "expected_doc": "sop_blood_transfusion.pdf",
        "expected_section": "12.0 Hemovigilance Committee Review and State Reporting Escalation",
        "expected_answer_snippet": "within 15 minutes",
    },
    # SOP 9: Emergency Code Response
    {
        "id": "q_emr_01",
        "question": "What is the required chest compression rate during adult CPR according to hospital standards?",
        "expected_doc": "sop_emergency_code_response.pdf",
        "expected_section": "5.0 High-Quality Cardiopulmonary Resuscitation (CPR) Benchmarks",
        "expected_answer_snippet": "100 to 120 chest compressions per minute",
    },
    {
        "id": "q_emr_02",
        "question": "How quickly is the hospital Rapid Response Team required to arrive at a Code Blue bedside?",
        "expected_doc": "sop_emergency_code_response.pdf",
        "expected_section": "4.0 Response Time Standards and Overhead Announcement",
        "expected_answer_snippet": "on scene within 3 minutes",
    },
    {
        "id": "q_emr_03",
        "question": "At what daily time must inpatient nursing units verify and seal the emergency crash cart?",
        "expected_doc": "sop_emergency_code_response.pdf",
        "expected_section": "9.0 Emergency Crash Cart Maintenance and Lock Auditing",
        "expected_answer_snippet": "daily by 08:00 AM",
    },
    {
        "id": "q_emr_04",
        "question": "How long after a cardiac arrest resuscitation must the detailed code log be documented in the electronic record?",
        "expected_doc": "sop_emergency_code_response.pdf",
        "expected_section": "11.0 Resuscitation Flow-Sheet Documentation in EMR",
        "expected_answer_snippet": "within 60 minutes post-event",
    },
    # SOP 10: Patient Identification
    {
        "id": "q_pid_01",
        "question": "What pieces of patient information are prohibited from being used as identifiers?",
        "expected_doc": "sop_patient_identification.pdf",
        "expected_section": "2.0 Approved Patient Identifiers and Prohibited Proxies",
        "expected_answer_snippet": "Room number and bed location are strictly prohibited",
    },
    {
        "id": "q_pid_02",
        "question": "What clinical meaning does a purple wristband indicate on an inpatient?",
        "expected_doc": "sop_patient_identification.pdf",
        "expected_section": "4.0 Color-Coded Alert Wristband Conventions",
        "expected_answer_snippet": "Purple indicates Do Not Resuscitate (DNR)",
    },
    {
        "id": "q_pid_03",
        "question": "How quickly must a destroyed or illegible patient identity wristband be replaced?",
        "expected_doc": "sop_patient_identification.pdf",
        "expected_section": "10.0 Damaged, Defaced, or Missing Band Replacement Workflow",
        "expected_answer_snippet": "within 10 minutes",
    },
    {
        "id": "q_pid_04",
        "question": "Within what time frame must a patient misidentification near-miss be escalated to the Risk Manager?",
        "expected_doc": "sop_patient_identification.pdf",
        "expected_section": "12.0 Near-Miss Reporting, Safety Review, and Incident Escalation",
        "expected_answer_snippet": "within 2 hours",
    },
    # SOP 11: Biomedical Waste
    {
        "id": "q_wst_01",
        "question": "At what fill level must sharps containers be sealed and replaced?",
        "expected_doc": "sop_biomedical_waste.pdf",
        "expected_section": "5.0 Sharps Management and Container Fill Limits",
        "expected_answer_snippet": "when 3/4 full",
    },
    {
        "id": "q_wst_02",
        "question": "What is the maximum allowed room-temperature storage duration for biohazardous waste before disposal?",
        "expected_doc": "sop_biomedical_waste.pdf",
        "expected_section": "7.0 Central Holding Area Storage Times and Temperature Controls",
        "expected_answer_snippet": "holding room is 48 hours",
    },
    {
        "id": "q_wst_03",
        "question": "What thickness and glove material is required for environmental staff handling regulated medical waste bags?",
        "expected_doc": "sop_biomedical_waste.pdf",
        "expected_section": "8.0 PPE Requirements: Heavy-Duty Utility Glove Standards",
        "expected_answer_snippet": "Heavy-duty 14-mil nitrile utility gloves",
    },
    {
        "id": "q_wst_04",
        "question": "How quickly must an employee sustaining an accidental needle-stick be seen for post-exposure prophylaxis?",
        "expected_doc": "sop_biomedical_waste.pdf",
        "expected_section": "10.0 Occupational Exposure Protocol (Sharps & Splashes)",
        "expected_answer_snippet": "for PEP within 2 hours",
    },
    # SOP 12: Pharmacy Storage
    {
        "id": "q_phr_01",
        "question": "What is the mandatory temperature range for hospital refrigerated pharmaceutical cold storage?",
        "expected_doc": "sop_pharmacy_storage.pdf",
        "expected_section": "2.0 Standard Temperature Range Specifications",
        "expected_answer_snippet": "2°C to 8°C (36°F to 46°F)",
    },
    {
        "id": "q_phr_02",
        "question": "How often do calibrated digital sensors log temperature readings in pharmacy refrigerators?",
        "expected_doc": "sop_pharmacy_storage.pdf",
        "expected_section": "3.0 Continuous Monitoring and NIST Data Logger Calibration",
        "expected_answer_snippet": "record temperatures every 15 minutes",
    },
    {
        "id": "q_phr_03",
        "question": "How frequently must perpetual inventory counts be conducted for Schedule II controlled substances?",
        "expected_doc": "sop_pharmacy_storage.pdf",
        "expected_section": "7.0 Controlled Substance Secure Storage (Schedule II-V)",
        "expected_answer_snippet": "counted every 24 hours",
    },
    {
        "id": "q_phr_04",
        "question": "What dollar value threshold of inventory loss from cold storage failure triggers escalation to the COO?",
        "expected_doc": "sop_pharmacy_storage.pdf",
        "expected_section": "12.0 Pharmacy Quality Auditing, Loss Reporting, and Escalation",
        "expected_answer_snippet": "product loss exceeding $10,000",
    },
]
