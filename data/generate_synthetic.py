"""Synthetic Medical Document and Policy Generator for MediDoc AI.

Generates realistic clinical documents (discharge summaries, lab reports) and
hospital standard operating procedures (SOPs) as multi-page PDFs using ReportLab.
Accompanied by ground-truth JSON files for clinical extraction and validation testing.

CRITICAL PRIVACY RULE:
All data generated is strictly synthetic. No real patient data or PII is used.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page counts."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int) -> None:
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4A5568"))

        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(
                54,
                11 * 72 - 36,
                "METROPOLITAN HEALTH SYSTEM — OFFICIAL CLINICAL/ADMINISTRATIVE DOCUMENT",
            )
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

        # Footer (All pages)
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 30, footer_text)
        self.drawString(
            54,
            30,
            "SYNTHETIC DOCUMENT — FOR SIMULATION & TESTING ONLY — NO REAL PATIENT DATA",
        )
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.5)
        self.line(54, 42, 8.5 * 72 - 54, 42)
        self.restoreState()


def get_document_styles() -> Dict[str, ParagraphStyle]:
    """Build consistent typography styles for synthetic documents."""
    base_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=base_styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        alignment=0,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#2B6CB0"),
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "DocH1",
        parent=base_styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#2C5282"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "DocH2",
        parent=base_styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "DocBody",
        parent=base_styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=6,
    )

    callout_style = ParagraphStyle(
        "DocCallout",
        parent=base_styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#742A2A"),
        spaceBefore=4,
        spaceAfter=6,
    )

    table_cell_style = ParagraphStyle(
        "DocTableCell",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1A202C"),
    )

    table_header_style = ParagraphStyle(
        "DocTableHeader",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "h1": h1_style,
        "h2": h2_style,
        "body": body_style,
        "callout": callout_style,
        "table_cell": table_cell_style,
        "table_header": table_header_style,
    }


# ============================================================================
# SOP GENERATORS (5 Multi-page Policies with Tables)
# ============================================================================


def generate_sop_infection_control(output_path: Path) -> None:
    """Generate multi-page SOP for Infection Control with isolation categories table."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = get_document_styles()
    story: List[Any] = []

    # Header block
    story.append(
        Paragraph("METROPOLITAN GENERAL HOSPITAL — POLICY & PROCEDURE", styles["subtitle"])
    )
    story.append(
        Paragraph(
            "STANDARD OPERATING PROCEDURE: INFECTION PREVENTION AND TRANSMISSION-BASED ISOLATION CONTROLS",
            styles["title"],
        )
    )
    story.append(
        Paragraph(
            "<b>Document ID:</b> SOP-INF-2026-01 | <b>Effective Date:</b> 2026-01-01 | <b>Review Cycle:</b> Annual | <b>Department:</b> Epidemiology & Quality",
            styles["body"],
        )
    )
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#2B6CB0"),
            spaceBefore=4,
            spaceAfter=10,
        )
    )

    story.append(Paragraph("1.0 Purpose and Operational Objective", styles["h1"]))
    story.append(
        Paragraph(
            "This standard operating procedure defines clinical guidelines and operational requirements "
            "for preventing hospital-acquired infections (HAIs) across inpatient wards, surgical suites, "
            "and intensive care units. The primary objective is early pathogen identification, effective barrier "
            "precautions, and safe decontamination workflows to minimize cross-transmission risk.",
            styles["body"],
        )
    )

    story.append(Paragraph("2.0 Scope and Regulatory Mandate", styles["h1"]))
    story.append(
        Paragraph(
            "This policy applies to all clinical personnel, nursing staff, allied healthcare providers, "
            "environmental services teams, and visiting observers. Compliance with CDC guidelines, WHO "
            "recommendations, and state department of health infection benchmarks is mandatory. Failure "
            "to adhere to isolation protocols triggers immediate clinical review.",
            styles["body"],
        )
    )

    story.append(Paragraph("3.0 Standard Universal Precautions & Hand Hygiene", styles["h1"]))
    story.append(
        Paragraph(
            "Hand hygiene must be performed according to the 'Five Moments for Hand Hygiene': (1) before "
            "touching a patient, (2) before clean/aseptic procedures, (3) after body fluid exposure risk, "
            "(4) after touching a patient, and (5) after touching patient surroundings. Alcohol-based hand rub "
            "(ABHR) with minimum 70% ethyl alcohol is standard, except when caring for patients with Clostridioides difficile, "
            "where soap and water friction washing for at least 20 seconds is mandatory.",
            styles["body"],
        )
    )

    story.append(PageBreak())

    # Page 2
    story.append(Paragraph("4.0 Transmission-Based Isolation Categories", styles["h1"]))
    story.append(
        Paragraph(
            "Patients confirmed or suspected of harboring epidemiological target pathogens must be "
            "placed on transmission-based precautions immediately upon clinical suspicion. The table below "
            "summarizes mandatory precautions, PPE requirements, and ventilation specifications.",
            styles["body"],
        )
    )

    table_data = [
        [
            Paragraph("Category", styles["table_header"]),
            Paragraph("Target Pathogens", styles["table_header"]),
            Paragraph("Mandatory PPE", styles["table_header"]),
            Paragraph("Room Ventilation / Placement", styles["table_header"]),
            Paragraph("Terminal Cleaning", styles["table_header"]),
        ],
        [
            Paragraph("<b>Contact</b>", styles["table_cell"]),
            Paragraph("MRSA, VRE, C. difficile, Acinetobacter", styles["table_cell"]),
            Paragraph("Gown and non-sterile gloves upon entry", styles["table_cell"]),
            Paragraph("Private room or cohorting; dedicated equipment", styles["table_cell"]),
            Paragraph("Sodium hypochlorite (bleach) 1:10 solution", styles["table_cell"]),
        ],
        [
            Paragraph("<b>Droplet</b>", styles["table_cell"]),
            Paragraph("Influenza, Neisseria meningitidis, Pertussis", styles["table_cell"]),
            Paragraph("Surgical mask + face shield within 6 feet", styles["table_cell"]),
            Paragraph("Private room; door may remain open", styles["table_cell"]),
            Paragraph("Standard hospital-grade disinfectant", styles["table_cell"]),
        ],
        [
            Paragraph("<b>Airborne</b>", styles["table_cell"]),
            Paragraph("M. tuberculosis, Measles, Varicella, SARS-CoV", styles["table_cell"]),
            Paragraph("Fit-tested N95 or PAPR respirator", styles["table_cell"]),
            Paragraph("AIIR negative pressure room (≥12 ACH, -2.5 Pa)", styles["table_cell"]),
            Paragraph("UV-C disinfection post-discharge + 1 hr air clear", styles["table_cell"]),
        ],
        [
            Paragraph("<b>Protective</b>", styles["table_cell"]),
            Paragraph("Neutropenic (<500 ANC), Allogeneic HSCT", styles["table_cell"]),
            Paragraph("Mask, surgical gown, strict sterile barrier", styles["table_cell"]),
            Paragraph("Positive pressure room (HEPA filtration ≥99.97%)", styles["table_cell"]),
            Paragraph("Daily sporicidal wiping; no fresh plants/flowers", styles["table_cell"]),
        ],
    ]

    t = Table(table_data, colWidths=[65, 115, 110, 115, 95])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#2B6CB0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7FAFC"), colors.white]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("5.0 Environmental Decontamination & Disinfection Timelines", styles["h1"]))
    story.append(
        Paragraph(
            "High-touch surfaces (bed rails, IV pumps, call buttons, computer workstations) must be cleaned "
            "at least twice daily and after patient discharge. Terminal room cleaning following discharge "
            "of an isolation patient requires a minimum contact wet time of 4 minutes for quaternary ammonium "
            "compounds and 10 minutes for bleach solutions. All environmental rounds are documented in the EMR log.",
            styles["body"],
        )
    )

    story.append(Paragraph("6.0 Clinical Governance, Audit, and Breach Escalation", styles["h1"]))
    story.append(
        Paragraph(
            "The Infection Control Committee conducts weekly unannounced observational audits across all units. "
            "Hand hygiene compliance targets are set at ≥95%. Any cluster of two or more nosocomial infections "
            "in the same unit within a 14-day window requires an immediate sentinel outbreak investigation "
            "and notification of the Chief Medical Officer within 4 hours.",
            styles["body"],
        )
    )

    doc.build(story, canvasmaker=NumberedCanvas)


def generate_sop_discharge_process(output_path: Path) -> None:
    """Generate multi-page SOP for Inpatient Discharge Planning and Transitions."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = get_document_styles()
    story: List[Any] = []

    story.append(
        Paragraph("METROPOLITAN HEALTH SYSTEM — POLICY & PROCEDURE", styles["subtitle"])
    )
    story.append(
        Paragraph(
            "STANDARD OPERATING PROCEDURE: INPATIENT DISCHARGE PROCESS AND CARE TRANSITIONS",
            styles["title"],
        )
    )
    story.append(
        Paragraph(
            "<b>Document ID:</b> SOP-DIS-2026-02 | <b>Effective Date:</b> 2026-01-01 | <b>Department:</b> Care Coordination & Inpatient Medicine",
            styles["body"],
        )
    )
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#2B6CB0"),
            spaceBefore=4,
            spaceAfter=10,
        )
    )

    story.append(Paragraph("1.0 Objective and Target Timelines", styles["h1"]))
    story.append(
        Paragraph(
            "Safe, timely discharge planning begins on admission. The goal of this protocol is to reduce "
            "preventable 30-day hospital readmissions, eliminate post-discharge adverse drug events, and "
            "ensure smooth coordination between hospital teams, post-acute facilities, and primary care physicians.",
            styles["body"],
        )
    )

    story.append(Paragraph("2.0 Clinical Sign-off and Summary Requirements", styles["h1"]))
    story.append(
        Paragraph(
            "The attending physician must complete and digitally sign the formal discharge summary within "
            "<b>24 hours</b> of patient departure. For patients transferring to skilled nursing facilities (SNF) "
            "or acute rehab, the preliminary discharge order, medication list, and transfer packet must be "
            "finalized prior to physical departure from the unit.",
            styles["body"],
        )
    )

    story.append(Paragraph("3.0 Medication Reconciliation Protocol", styles["h1"]))
    story.append(
        Paragraph(
            "A clinical pharmacist or dedicated discharge nurse must perform three-way medication reconciliation: "
            "comparing pre-admission medications, active inpatient medications, and intended outpatient prescriptions. "
            "Every prescribed medication must have an explicitly documented indication, dosage, dosage unit, "
            "administration frequency, and intended treatment duration. Verbal instructions alone are prohibited.",
            styles["body"],
        )
    )

    story.append(PageBreak())

    # Page 2
    story.append(Paragraph("4.0 Staged Discharge Workflow and Responsibilities", styles["h1"]))
    story.append(
        Paragraph(
            "To achieve the target hospital departure cutoff of 11:00 AM, clinical teams must adhere to the "
            "phased milestones detailed below.",
            styles["body"],
        )
    )

    table_data = [
        [
            Paragraph("Workflow Stage", styles["table_header"]),
            Paragraph("Target Milestone", styles["table_header"]),
            Paragraph("Lead Role", styles["table_header"]),
            Paragraph("Mandatory Deliverables", styles["table_header"]),
        ],
        [
            Paragraph("<b>Pre-Discharge T-24h</b>", styles["table_cell"]),
            Paragraph("Day prior by 16:00", styles["table_cell"]),
            Paragraph("Attending / Resident", styles["table_cell"]),
            Paragraph("Identify anticipated discharge; draft medication list; verify ride home", styles["table_cell"]),
        ],
        [
            Paragraph("<b>Morning Review T-4h</b>", styles["table_cell"]),
            Paragraph("Day of discharge 07:30", styles["table_cell"]),
            Paragraph("Care Coordinator", styles["table_cell"]),
            Paragraph("Confirm DME delivery; finalize insurance approval; verify rehab bed", styles["table_cell"]),
        ],
        [
            Paragraph("<b>Medication Finalization</b>", styles["table_cell"]),
            Paragraph("Day of discharge 09:00", styles["table_cell"]),
            Paragraph("Clinical Pharmacist", styles["table_cell"]),
            Paragraph("Resolve drug discrepancies; complete bedside 'Meds-to-Beds' delivery", styles["table_cell"]),
        ],
        [
            Paragraph("<b>Patient Education</b>", styles["table_cell"]),
            Paragraph("Day of discharge 10:00", styles["table_cell"]),
            Paragraph("Primary Nurse", styles["table_cell"]),
            Paragraph("Teach-back technique for 'Red Flag' symptoms; review follow-up schedule", styles["table_cell"]),
        ],
        [
            Paragraph("<b>Departure & Transport</b>", styles["table_cell"]),
            Paragraph("Day of discharge 11:00", styles["table_cell"]),
            Paragraph("Unit Charge Nurse", styles["table_cell"]),
            Paragraph("Wheelchair escort to exit; update bed tracking system to dirty/cleaning", styles["table_cell"]),
        ],
    ]

    t = Table(table_data, colWidths=[90, 80, 95, 185])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#2B6CB0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7FAFC"), colors.white]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("5.0 Post-Discharge Follow-Up and Escalation Criteria", styles["h1"]))
    story.append(
        Paragraph(
            "High-risk patients (LACE score ≥ 10 or multi-morbid conditions) must receive a telephone follow-up "
            "call from the care transition team within <b>48 to 72 hours</b> post-discharge. The call must assess: "
            "(1) medication understanding and pharmacy pickup, (2) red flag warning signs (chest pain, worsening dyspnea, "
            "fever > 38.3°C, sudden wound drainage), (3) confirmed appointment with outpatient provider within 7 days. "
            "Any unresolved critical symptoms require immediate triage to the urgent care clinic or emergency department.",
            styles["body"],
        )
    )

    doc.build(story, canvasmaker=NumberedCanvas)


def generate_sop_billing_financial(output_path: Path) -> None:
    """Generate multi-page SOP for Hospital Billing, Authorization, and Disputes."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = get_document_styles()
    story: List[Any] = []

    story.append(
        Paragraph("METROPOLITAN HEALTH SYSTEM — ADMINISTRATIVE POLICY", styles["subtitle"])
    )
    story.append(
        Paragraph(
            "STANDARD OPERATING PROCEDURE: PATIENT FINANCIAL CLEARANCE, BILLING, AND DISPUTE RESOLUTION",
            styles["title"],
        )
    )
    story.append(
        Paragraph(
            "<b>Document ID:</b> SOP-BIL-2026-03 | <b>Effective Date:</b> 2026-01-01 | <b>Department:</b> Revenue Cycle & Patient Access",
            styles["body"],
        )
    )
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#2B6CB0"),
            spaceBefore=4,
            spaceAfter=10,
        )
    )

    story.append(Paragraph("1.0 Policy Purpose and Financial Ethics", styles["h1"]))
    story.append(
        Paragraph(
            "Metropolitan Health System is committed to transparent, accurate, and fair medical billing practices. "
            "This procedure outlines pre-service financial clearance, insurance authorization requirements, patient "
            "cost estimation under the No Surprises Act, and formal pathways for disputed charges.",
            styles["body"],
        )
    )

    story.append(Paragraph("2.0 Pre-Service Authorization Timelines", styles["h1"]))
    story.append(
        Paragraph(
            "For elective inpatient admissions and non-emergent surgical interventions, commercial and governmental "
            "payer pre-authorizations must be secured no later than <b>72 hours prior</b> to scheduled admission. "
            "Emergency admissions bypass pre-authorization, but patient access staff must submit an urgent clinical "
            "admission notification to the payer within <b>24 hours</b> of bed placement.",
            styles["body"],
        )
    )

    story.append(Paragraph("3.0 Good Faith Estimates (GFE)", styles["h1"]))
    story.append(
        Paragraph(
            "Uninsured and self-pay patients must be provided with a Good Faith Estimate within 1 business day of "
            "scheduling if the service is at least 3 business days out, or within 3 business days if scheduled at "
            "least 10 business days in advance. Discrepancies exceeding $400 entitle patients to external arbitration.",
            styles["body"],
        )
    )

    story.append(PageBreak())

    # Page 2
    story.append(Paragraph("4.0 Billing Service Categories and Dispute Windows", styles["h1"]))
    story.append(
        Paragraph(
            "Standard hospital billing rates, pre-authorization criteria, and patient appeal windows are structured "
            "by service class as shown in the schedule below.",
            styles["body"],
        )
    )

    table_data = [
        [
            Paragraph("Service Code / Tier", styles["table_header"]),
            Paragraph("Category Description", styles["table_header"]),
            Paragraph("Payer Pre-Auth Window", styles["table_header"]),
            Paragraph("Patient Appeal Window", styles["table_header"]),
            Paragraph("Escalation Authority", styles["table_header"]),
        ],
        [
            Paragraph("<b>INP-EMERG-01</b>", styles["table_cell"]),
            Paragraph("Emergency Inpatient Admission", styles["table_cell"]),
            Paragraph("Within 24 hrs post-bed placement", styles["table_cell"]),
            Paragraph("60 days from final bill date", styles["table_cell"]),
            Paragraph("Utilization Review Director", styles["table_cell"]),
        ],
        [
            Paragraph("<b>INP-ELECT-02</b>", styles["table_cell"]),
            Paragraph("Elective Inpatient Surgery", styles["table_cell"]),
            Paragraph("Minimum 72 hrs pre-op", styles["table_cell"]),
            Paragraph("45 days from statement date", styles["table_cell"]),
            Paragraph("Revenue Cycle Manager", styles["table_cell"]),
        ],
        [
            Paragraph("<b>OUT-DIAG-03</b>", styles["table_cell"]),
            Paragraph("Advanced Imaging (CT, MRI, PET)", styles["table_cell"]),
            Paragraph("48 hrs prior to imaging scan", styles["table_cell"]),
            Paragraph("30 days from billing statement", styles["table_cell"]),
            Paragraph("Patient Accounts Supervisor", styles["table_cell"]),
        ],
        [
            Paragraph("<b>ICU-CRIT-04</b>", styles["table_cell"]),
            Paragraph("Critical Care & ECMO Services", styles["table_cell"]),
            Paragraph("Daily concurrent clinical review", styles["table_cell"]),
            Paragraph("90 days from statement date", styles["table_cell"]),
            Paragraph("Chief Financial Officer", styles["table_cell"]),
        ],
    ]

    t = Table(table_data, colWidths=[90, 110, 100, 85, 95])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#2B6CB0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7FAFC"), colors.white]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("5.0 Dispute Resolution and Financial Hardship Policy", styles["h1"]))
    story.append(
        Paragraph(
            "Patients contesting line-item charges or billing calculations must submit an itemized dispute form. "
            "Billing holds are placed immediately upon receipt of a dispute, suspending all collection activity. "
            "The Billing Resolution Committee must issue a formal determination within <b>30 calendar days</b>. "
            "Patients whose household income falls below 250% of the Federal Poverty Level (FPL) are eligible for "
            "100% charity care write-offs under the Hospital Financial Assistance Program.",
            styles["body"],
        )
    )

    doc.build(story, canvasmaker=NumberedCanvas)


def generate_sop_medication_safety(output_path: Path) -> None:
    """Generate multi-page SOP for High-Alert Medication Safety and Administration."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = get_document_styles()
    story: List[Any] = []

    story.append(
        Paragraph("METROPOLITAN HEALTH SYSTEM — CLINICAL PHARMACY POLICY", styles["subtitle"])
    )
    story.append(
        Paragraph(
            "STANDARD OPERATING PROCEDURE: HIGH-ALERT MEDICATION SAFETY AND INFUSION CONTROLS",
            styles["title"],
        )
    )
    story.append(
        Paragraph(
            "<b>Document ID:</b> SOP-MED-2026-04 | <b>Effective Date:</b> 2026-01-01 | <b>Department:</b> Pharmacy & Therapeutics Committee",
            styles["body"],
        )
    )
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#2B6CB0"),
            spaceBefore=4,
            spaceAfter=10,
        )
    )

    story.append(Paragraph("1.0 Safety Mandate & High-Alert Classification", styles["h1"]))
    story.append(
        Paragraph(
            "High-alert medications bear a heightened risk of causing significant patient harm when used in error. "
            "Although errors may not occur more frequently with these drugs, the clinical consequences are catastrophic. "
            "This protocol enforces strict prescribing safeguards, smart infusion pump guardrails, and independent "
            "double-checks for all designated high-alert pharmaceuticals.",
            styles["body"],
        )
    )

    story.append(Paragraph("2.0 Five Rights and Independent Double-Check Protocol", styles["h1"]))
    story.append(
        Paragraph(
            "Prior to administering any high-alert medication, two licensed nurses must independently verify: "
            "(1) the right patient using two unique identifiers, (2) right medication, (3) right dose and concentration, "
            "(4) right route, and (5) right time and infusion rate. The double-check must be documented in the electronic "
            "medication administration record (eMAR) with dual clinician signatures.",
            styles["body"],
        )
    )

    story.append(Paragraph("3.0 Look-Alike / Sound-Alike (LASA) and Tall-Man Lettering", styles["h1"]))
    story.append(
        Paragraph(
            "All pharmacy labels and automated dispensing cabinet (ADC) storage bins must utilize FDA/ISMP "
            "Tall-Man lettering (e.g., DOBUTamine vs. DOPamine, hydrOXYzine vs. hydrALAZINE). Automated cabinets "
            "must enforce lock-out barriers for concentrated electrolytes.",
            styles["body"],
        )
    )

    story.append(PageBreak())

    # Page 2
    story.append(Paragraph("4.0 High-Alert Medication Dosing and Monitoring Guardrails", styles["h1"]))
    story.append(
        Paragraph(
            "The table below specifies mandatory dosing boundaries, maximum infusion rates, and clinical monitoring "
            "parameters for high-alert drug classes across all inpatient divisions.",
            styles["body"],
        )
    )

    table_data = [
        [
            Paragraph("Medication Class", styles["table_header"]),
            Paragraph("Exemplar Agent", styles["table_header"]),
            Paragraph("Absolute Dosing Guardrail", styles["table_header"]),
            Paragraph("Required Clinical Monitoring", styles["table_header"]),
            Paragraph("Antidote / Reversal Agent", styles["table_header"]),
        ],
        [
            Paragraph("<b>Concentrated Potassium</b>", styles["table_cell"]),
            Paragraph("Potassium Chloride IV", styles["table_cell"]),
            Paragraph("Max 40 mEq/L peripheral; NEVER IV push", styles["table_cell"]),
            Paragraph("Continuous ECG monitoring if >10 mEq/hr; serum K+ q4h", styles["table_cell"]),
            Paragraph("Calcium gluconate, Insulin + D50W", styles["table_cell"]),
        ],
        [
            Paragraph("<b>Intravenous Anticoagulants</b>", styles["table_cell"]),
            Paragraph("Heparin Sodium Continuous IV", styles["table_cell"]),
            Paragraph("Initial bolus 80 units/kg; max 20,000 U/day", styles["table_cell"]),
            Paragraph("anti-Xa or aPTT every 6 hours; daily platelet count", styles["table_cell"]),
            Paragraph("Protamine Sulfate (1 mg per 100 U heparin)", styles["table_cell"]),
        ],
        [
            Paragraph("<b>Intravenous Regular Insulin</b>", styles["table_cell"]),
            Paragraph("Regular Insulin IV Infusion", styles["table_cell"]),
            Paragraph("Max titration 0.1 units/kg/hr without MD order", styles["table_cell"]),
            Paragraph("Point-of-care blood glucose hourly until stable 4 hrs", styles["table_cell"]),
            Paragraph("Dextrose 50% IV injection (25 g)", styles["table_cell"]),
        ],
        [
            Paragraph("<b>Intravenous Opioids</b>", styles["table_cell"]),
            Paragraph("Morphine / Hydromorphone PCA", styles["table_cell"]),
            Paragraph("Basal infusion restricted; lockout min 6 min", styles["table_cell"]),
            Paragraph("Continuous SpO2 and capnography; RASS score q2h", styles["table_cell"]),
            Paragraph("Naloxone 0.04-0.4 mg IV titration", styles["table_cell"]),
        ],
    ]

    t = Table(table_data, colWidths=[90, 85, 110, 115, 80])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#2B6CB0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7FAFC"), colors.white]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("5.0 Adverse Drug Event (ADE) Reporting and Root Cause Analysis", styles["h1"]))
    story.append(
        Paragraph(
            "Any medication incident resulting in patient harm or categorized as a 'near-miss' involving high-alert "
            "medications must be logged in the Safety Incident Management System within <b>2 hours</b>. The clinical "
            "pharmacy director initiates a multi-disciplinary root cause analysis (RCA) within 5 business days to determine "
            "systemic vulnerabilities and implement error-proofing constraints.",
            styles["body"],
        )
    )

    doc.build(story, canvasmaker=NumberedCanvas)


def generate_sop_patient_consent(output_path: Path) -> None:
    """Generate multi-page SOP for Informed Consent for Clinical Procedures."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = get_document_styles()
    story: List[Any] = []

    story.append(
        Paragraph("METROPOLITAN HEALTH SYSTEM — CLINICAL GOVERNANCE", styles["subtitle"])
    )
    story.append(
        Paragraph(
            "STANDARD OPERATING PROCEDURE: INFORMED CONSENT FOR CLINICAL PROCEDURES AND RESEARCH",
            styles["title"],
        )
    )
    story.append(
        Paragraph(
            "<b>Document ID:</b> SOP-CON-2026-05 | <b>Effective Date:</b> 2026-01-01 | <b>Department:</b> Medical Staff Affairs & Legal Counsel",
            styles["body"],
        )
    )
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#2B6CB0"),
            spaceBefore=4,
            spaceAfter=10,
        )
    )

    story.append(Paragraph("1.0 Fundamental Legal & Ethical Principles", styles["h1"]))
    story.append(
        Paragraph(
            "Every adult patient with decision-making capacity possesses the fundamental moral and legal right to "
            "determine what medical interventions are performed upon their body. Informed consent is a shared clinical "
            "dialogue, not merely the signing of a form. Clinicians must explain the nature of the condition, proposed "
            "procedure, material risks, potential benefits, and reasonable alternatives, including no intervention.",
            styles["body"],
        )
    )

    story.append(Paragraph("2.0 Clinician Responsibility & Prohibition of Delegation", styles["h1"]))
    story.append(
        Paragraph(
            "The practitioner who will perform the procedure is legally responsible for discussing and obtaining "
            "informed consent. This duty <b>may not be delegated</b> to registered nurses, medical assistants, or unit clerks. "
            "A registered nurse may only witness the patient's signature confirming identity and voluntary signing.",
            styles["body"],
        )
    )

    story.append(Paragraph("3.0 Decision-Making Capacity and Surrogate Decision-Makers", styles["h1"]))
    story.append(
        Paragraph(
            "In patients lacking decision-making capacity due to delirium, coma, or dementia, consent must be obtained "
            "from the legal healthcare surrogate in following hierarchical sequence: (1) designated healthcare proxy / "
            "Durable Power of Attorney for Healthcare, (2) court-appointed guardian, (3) spouse, (4) adult children, "
            "(5) parents, and (6) adult siblings.",
            styles["body"],
        )
    )

    story.append(PageBreak())

    # Page 2
    story.append(Paragraph("4.0 Procedure Risk Classification and Consent Documentation", styles["h1"]))
    story.append(
        Paragraph(
            "The table below details consent tiers, mandatory provider credentials, documentation requirements, "
            "and validity expiration periods across clinical services.",
            styles["body"],
        )
    )

    table_data = [
        [
            Paragraph("Procedure Risk Tier", styles["table_header"]),
            Paragraph("Exemplar Procedures", styles["table_header"]),
            Paragraph("Authorized Provider", styles["table_header"]),
            Paragraph("Required Form & Signatures", styles["table_header"]),
            Paragraph("Validity Window", styles["table_header"]),
        ],
        [
            Paragraph("<b>Tier 1: Non-Invasive</b>", styles["table_cell"]),
            Paragraph("Phlebotomy, standard X-ray, ECG, wound dressing", styles["table_cell"]),
            Paragraph("Treating physician or licensed staff nurse", styles["table_cell"]),
            Paragraph("General admission agreement; verbal assent in chart", styles["table_cell"]),
            Paragraph("Duration of inpatient stay", styles["table_cell"]),
        ],
        [
            Paragraph("<b>Tier 2: Minor Invasive</b>", styles["table_cell"]),
            Paragraph("Lumbar puncture, paracentesis, central venous line", styles["table_cell"]),
            Paragraph("Attending physician, fellow, or credentialed resident", styles["table_cell"]),
            Paragraph("Specialized Form CON-202 + witness signature", styles["table_cell"]),
            Paragraph("30 days unless condition changes", styles["table_cell"]),
        ],
        [
            Paragraph("<b>Tier 3: Major Operative</b>", styles["table_cell"]),
            Paragraph("General anesthesia surgery, cardiac catheterization", styles["table_cell"]),
            Paragraph("Operating surgeon / interventional attending only", styles["table_cell"]),
            Paragraph("Formal Surgical Form CON-301 + patient + surgeon sig", styles["table_cell"]),
            Paragraph("30 days maximum pre-procedure", styles["table_cell"]),
        ],
        [
            Paragraph("<b>Tier 4: Emergency Exception</b>", styles["table_cell"]),
            Paragraph("Imminent risk to life, limb, or neurological viability", styles["table_cell"]),
            Paragraph("Two independent licensed attending physicians", styles["table_cell"]),
            Paragraph("Emergency Consent Waiver Form CON-911 in chart", styles["table_cell"]),
            Paragraph("Single emergent episode only", styles["table_cell"]),
        ],
    ]

    t = Table(table_data, colWidths=[90, 110, 100, 100, 80])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#2B6CB0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7FAFC"), colors.white]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("5.0 Emergency Doctrine & Right to Revocation", styles["h1"]))
    story.append(
        Paragraph(
            "Under the emergency exception doctrine, life-saving care may proceed when a patient is unconscious "
            "or incapacitated and immediate family cannot be reached within clinically acceptable response times. "
            "Two attending physicians must document in the medical record that delay would risk irreversible injury or death. "
            "Patients retain the absolute right to revoke consent at any time prior to the induction of anesthesia or "
            "procedure initiation, in which case the procedure must stop immediately unless doing so would cause imminent death.",
            styles["body"],
        )
    )

    doc.build(story, canvasmaker=NumberedCanvas)


# ============================================================================
# CLINICAL REPORT GENERATOR (Discharge Summaries & Lab Reports)
# ============================================================================


def generate_clinical_report_pdf(
    output_path: Path,
    report_title: str,
    patient_data: Dict[str, Any],
    admission_date: str,
    discharge_date: str,
    diagnosis_list: List[str],
    medications_list: List[Dict[str, Any]],
    summary_text: str,
    extra_sections: Optional[List[Dict[str, Any]]] = None,
    deliberate_error_note: Optional[str] = None,
) -> None:
    """Generate a realistic clinical report PDF with patient header, meds table, and summary."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = get_document_styles()
    story: List[Any] = []

    # Hospital Banner
    story.append(
        Paragraph("METROPOLITAN UNIVERSITY MEDICAL CENTER", styles["subtitle"])
    )
    story.append(Paragraph(report_title.upper(), styles["title"]))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#2B6CB0"),
            spaceBefore=2,
            spaceAfter=8,
        )
    )

    # Patient Demographics Table
    patient_name = patient_data.get("name", "UNSPECIFIED")
    patient_age = patient_data.get("age", "N/A")
    patient_sex = patient_data.get("sex", "N/A")
    patient_mrn = patient_data.get("mrn", "MRN-SYNTH-000")
    patient_phone = patient_data.get("phone", "555-000-0000")
    patient_email = patient_data.get("email", "patient@fake-hospital.org")

    demo_data = [
        [
            Paragraph(f"<b>Patient Name:</b> {patient_name}", styles["body"]),
            Paragraph(f"<b>MRN:</b> {patient_mrn}", styles["body"]),
            Paragraph(f"<b>Age / Sex:</b> {patient_age} yrs / {patient_sex}", styles["body"]),
        ],
        [
            Paragraph(f"<b>Admission Date:</b> {admission_date}", styles["body"]),
            Paragraph(f"<b>Discharge Date:</b> {discharge_date}", styles["body"]),
            Paragraph(f"<b>Contact:</b> {patient_phone}", styles["body"]),
        ],
        [
            Paragraph(f"<b>Patient Email:</b> {patient_email}", styles["body"]),
            Paragraph("<b>Facility:</b> Main Hospital Pavilion", styles["body"]),
            Paragraph("<b>Attending:</b> Dr. S. Patel, MD (Synthetic)", styles["body"]),
        ],
    ]

    t_demo = Table(demo_data, colWidths=[170, 150, 160])
    t_demo.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_demo)
    story.append(Spacer(1, 10))

    # Diagnoses Section
    story.append(Paragraph("PRIMARY & SECONDARY DIAGNOSES", styles["h1"]))
    if diagnosis_list:
        for diag in diagnosis_list:
            story.append(Paragraph(f"• {diag}", styles["body"]))
    else:
        story.append(
            Paragraph(
                "<i>[No diagnoses entered in electronic chart - pending clinician entry]</i>",
                styles["callout"],
            )
        )
    story.append(Spacer(1, 6))

    # Discharge / Prescribed Medications Table
    story.append(Paragraph("DISCHARGE MEDICATIONS & REGIMEN", styles["h1"]))
    med_table_data = [
        [
            Paragraph("Medication Name", styles["table_header"]),
            Paragraph("Dose", styles["table_header"]),
            Paragraph("Unit", styles["table_header"]),
            Paragraph("Frequency / Instructions", styles["table_header"]),
        ]
    ]

    for med in medications_list:
        med_name = med.get("name", "Unknown")
        dose_val = str(med.get("dose", ""))
        unit_val = med.get("unit", "")
        if not unit_val:
            unit_display = "<b>[MISSING UNIT]</b>"
        else:
            unit_display = unit_val
        freq_val = med.get("frequency", "")

        med_table_data.append(
            [
                Paragraph(med_name, styles["table_cell"]),
                Paragraph(dose_val, styles["table_cell"]),
                Paragraph(unit_display, styles["table_cell"]),
                Paragraph(freq_val, styles["table_cell"]),
            ]
        )

    t_med = Table(med_table_data, colWidths=[150, 60, 80, 190])
    t_med.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C5282")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#2C5282")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_med)
    story.append(Spacer(1, 10))

    # Extra sections if provided (e.g. lab table, vitals)
    if extra_sections:
        for sec in extra_sections:
            sec_title = sec.get("title", "Clinical Details")
            story.append(Paragraph(sec_title, styles["h1"]))
            if "table" in sec:
                t_sec = Table(sec["table"]["data"], colWidths=sec["table"].get("colWidths", None))
                t_sec.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A5568")),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#4A5568")),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                story.append(t_sec)
                story.append(Spacer(1, 8))
            if "text" in sec:
                story.append(Paragraph(sec["text"], styles["body"]))
                story.append(Spacer(1, 6))

    # Clinical Summary
    story.append(Paragraph("HOSPITAL COURSE & CLINICIAN SUMMARY", styles["h1"]))
    story.append(Paragraph(summary_text, styles["body"]))
    story.append(Spacer(1, 10))

    # Sign-off block
    sign_block = [
        Paragraph("<b>Attending Clinician:</b> Dr. Sharon Patel, MD, FACP", styles["body"]),
        Paragraph("<b>Electronic Signature Verified:</b> Yes | <b>Date/Time:</b> Auto-generated", styles["body"]),
    ]
    story.append(KeepTogether(sign_block))

    doc.build(story, canvasmaker=NumberedCanvas)


def get_synthetic_reports_dataset() -> List[Dict[str, Any]]:
    """Define 8 synthetic clinical reports (discharge summaries & lab reports).

    Includes clean reports as well as deliberate error reports covering all 4 validation rules:
    1. discharge_date before admission_date
    2. missing medication dose unit
    3. empty diagnosis list
    4. patient age out of range (0-120)
    """
    reports: List[Dict[str, Any]] = [
        # 1. Clean Cardiology Discharge Summary
        {
            "filename_stem": "discharge_summary_01_cardiac",
            "report_title": "Inpatient Discharge Summary - Cardiology Service",
            "patient": {"name": "Arthur Pendelton", "age": 67, "sex": "M"},
            "demographics": {
                "mrn": "MRN-2026-89102",
                "phone": "555-014-9821",
                "email": "arthur.p.synth@example-hospital.org",
            },
            "admission_date": "2026-01-10",
            "discharge_date": "2026-01-15",
            "diagnosis": [
                "Acute Non-ST Elevation Myocardial Infarction (NSTEMI)",
                "Essential Primary Hypertension",
                "Atherosclerotic Heart Disease",
                "Hyperlipidemia",
            ],
            "medications": [
                {"name": "Aspirin", "dose": 81, "unit": "mg", "frequency": "Daily orally"},
                {"name": "Clopidogrel", "dose": 75, "unit": "mg", "frequency": "Daily orally"},
                {"name": "Atorvastatin", "dose": 40, "unit": "mg", "frequency": "Nightly orally"},
                {"name": "Metoprolol Succinate", "dose": 50, "unit": "mg", "frequency": "Daily orally"},
            ],
            "summary": (
                "67-year-old male admitted with acute non-ST elevation myocardial infarction. Coronary angiography "
                "revealed 90% proximal LAD stenosis, successfully treated with a drug-eluting stent. Post-procedure "
                "echocardiogram showed preserved LVEF of 50%. Patient achieved stable recovery, transitioned to oral "
                "dual antiplatelet therapy, and was discharged in good clinical condition with outpatient cardiology follow-up."
            ),
            "deliberate_errors": [],
            "extra_sections": None,
        },
        # 2. Clean Pulmonology Discharge Summary
        {
            "filename_stem": "discharge_summary_02_pulmonary",
            "report_title": "Inpatient Discharge Summary - Pulmonary Medicine",
            "patient": {"name": "Eleanor Vance", "age": 54, "sex": "F"},
            "demographics": {
                "mrn": "MRN-2026-44129",
                "phone": "555-017-3329",
                "email": "eleanor.v.synth@example-hospital.org",
            },
            "admission_date": "2026-02-03",
            "discharge_date": "2026-02-08",
            "diagnosis": [
                "Community-Acquired Lobar Pneumonia",
                "Acute Exacerbation of COPD",
                "Mild Hypoxemia",
            ],
            "medications": [
                {"name": "Azithromycin", "dose": 500, "unit": "mg", "frequency": "Daily orally"},
                {"name": "Prednisone", "dose": 20, "unit": "mg", "frequency": "Daily taper for 5 days"},
                {"name": "Albuterol-Ipratropium", "dose": 2.5, "unit": "mg", "frequency": "Inhalation every 6 hrs PRN"},
            ],
            "summary": (
                "54-year-old female with known COPD admitted with fever, cough, and right lower lobe consolidation. "
                "Treated with IV ceftriaxone and azithromycin with marked symptomatic improvement. Weaned to room air "
                "with resting SpO2 96%. Discharged with oral antibiotic step-down and pulmonary rehabilitation referral."
            ),
            "deliberate_errors": [],
            "extra_sections": None,
        },
        # 3. Clean Orthopedic Discharge Summary
        {
            "filename_stem": "discharge_summary_03_orthopedic",
            "report_title": "Inpatient Discharge Summary - Orthopedic Surgery",
            "patient": {"name": "Carlos Santana-Ramirez", "age": 72, "sex": "M"},
            "demographics": {
                "mrn": "MRN-2026-77218",
                "phone": "555-019-8812",
                "email": "carlos.sr.fake@example-hospital.org",
            },
            "admission_date": "2026-02-14",
            "discharge_date": "2026-02-19",
            "diagnosis": [
                "Severe Primary Osteoarthritis Right Hip",
                "Post-Surgical Status Post Right Total Hip Arthroplasty",
                "Postoperative Anemia",
            ],
            "medications": [
                {"name": "Apixaban", "dose": 2.5, "unit": "mg", "frequency": "Twice daily orally for 35 days"},
                {"name": "Acetaminophen", "dose": 650, "unit": "mg", "frequency": "Every 6 hours PRN orally"},
                {"name": "Ferrous Sulfate", "dose": 325, "unit": "mg", "frequency": "Daily orally"},
                {"name": "Oxycodone", "dose": 5, "unit": "mg", "frequency": "Every 6 hours PRN for breakthrough pain"},
            ],
            "summary": (
                "72-year-old male admitted for elective right total hip arthroplasty under spinal anesthesia. "
                "Procedure uncomplicated. Physical therapy initiated post-op day 1 with progressive weight-bearing as tolerated. "
                "Surgical incision clean, dry, and intact with staples in situ. Patient cleared for home discharge with home health PT."
            ),
            "deliberate_errors": [],
            "extra_sections": None,
        },
        # 4. Deliberate Error 1: Discharge date BEFORE admission date
        {
            "filename_stem": "discharge_summary_04_error_dates",
            "report_title": "Inpatient Discharge Summary - General Surgery",
            "patient": {"name": "David K. Bowman", "age": 41, "sex": "M"},
            "demographics": {
                "mrn": "MRN-2026-90114",
                "phone": "555-011-4521",
                "email": "david.b.synth@example-hospital.org",
            },
            "admission_date": "2026-03-12",
            "discharge_date": "2026-03-08",  # Deliberate Error: 4 days before admission
            "diagnosis": [
                "Acute Appendicitis with Localized Peritonitis",
                "Status Post Laparoscopic Appendectomy",
            ],
            "medications": [
                {"name": "Cephalexin", "dose": 500, "unit": "mg", "frequency": "Four times daily for 7 days"},
                {"name": "Ibuprofen", "dose": 400, "unit": "mg", "frequency": "Every 6 hours PRN with meals"},
            ],
            "summary": (
                "41-year-old male presenting with acute right lower quadrant abdominal pain and leukocytosis. "
                "Laparoscopic appendectomy performed with uncomplicated intraoperative course. Tolerating regular diet, "
                "ambulating independently, pain controlled on oral analgesics. Note: administrative dates reflect clerical error."
            ),
            "deliberate_errors": [
                {
                    "field": "discharge_date",
                    "rule": "discharge_date_before_admission",
                    "severity": "error",
                    "message": "discharge_date (2026-03-08) must not be before admission_date (2026-03-12)",
                }
            ],
            "extra_sections": None,
        },
        # 5. Deliberate Error 2: Missing medication dose unit
        {
            "filename_stem": "discharge_summary_05_error_med_unit",
            "report_title": "Inpatient Discharge Summary - Endocrinology Service",
            "patient": {"name": "Beatrice Morales", "age": 62, "sex": "F"},
            "demographics": {
                "mrn": "MRN-2026-11883",
                "phone": "555-013-7729",
                "email": "beatrice.m.fake@example-hospital.org",
            },
            "admission_date": "2026-03-01",
            "discharge_date": "2026-03-05",
            "diagnosis": [
                "Type 2 Diabetes Mellitus with Hyperglycemia",
                "Diabetic Peripheral Neuropathy",
                "Hypertension",
            ],
            "medications": [
                {"name": "Metformin", "dose": 500, "unit": "mg", "frequency": "Twice daily with meals"},
                {"name": "Gabapentin", "dose": 300, "unit": "", "frequency": "Nightly orally"},  # Deliberate Error: missing unit
                {"name": "Lisinopril", "dose": 10, "unit": "mg", "frequency": "Daily orally"},
            ],
            "summary": (
                "62-year-old female admitted for severe hyperglycemia without ketoacidosis (glucose 420 mg/dL). "
                "Rehydrated and transitioned from insulin infusion to oral regimen. Neuropathic pain management initiated. "
                "Patient educated on glucometer monitoring and lifestyle interventions. Discharged stable."
            ),
            "deliberate_errors": [
                {
                    "field": "medications[1].unit",
                    "rule": "medication_missing_unit",
                    "severity": "error",
                    "message": "every medication must have a dose and a unit (Gabapentin unit is empty)",
                }
            ],
            "extra_sections": None,
        },
        # 6. Deliberate Error 3: Empty diagnosis list
        {
            "filename_stem": "discharge_summary_06_error_empty_diagnosis",
            "report_title": "Inpatient Discharge Summary - Acute Observation Unit",
            "patient": {"name": "Fiona Gallagher-Smith", "age": 33, "sex": "F"},
            "demographics": {
                "mrn": "MRN-2026-66231",
                "phone": "555-018-2234",
                "email": "fiona.gs.synth@example-hospital.org",
            },
            "admission_date": "2026-03-15",
            "discharge_date": "2026-03-17",
            "diagnosis": [],  # Deliberate Error: empty diagnosis list
            "medications": [
                {"name": "Amoxicillin-Clavulanate", "dose": 875, "unit": "mg", "frequency": "Twice daily for 7 days"},
                {"name": "Probiotic", "dose": 1, "unit": "capsule", "frequency": "Daily orally"},
            ],
            "summary": (
                "33-year-old female admitted for observation following acute abdominal cramping and mild fever. "
                "Ultrasound and inflammatory markers remained unrevealing. Symptoms resolved spontaneously on empiric "
                "supportive management. Discharged home with instructions to return if fevers recrudesce."
            ),
            "deliberate_errors": [
                {
                    "field": "diagnosis",
                    "rule": "diagnosis_empty",
                    "severity": "error",
                    "message": "diagnosis list is not empty (found 0 diagnoses)",
                }
            ],
            "extra_sections": None,
        },
        # 7. Clean Lab Report: Comprehensive Metabolic & Renal Panel
        {
            "filename_stem": "lab_report_01_metabolic",
            "report_title": "Laboratory & Diagnostic Clinical Report - Renal Service",
            "patient": {"name": "George Sterling", "age": 58, "sex": "M"},
            "demographics": {
                "mrn": "MRN-2026-33901",
                "phone": "555-012-6643",
                "email": "george.s.synth@example-hospital.org",
            },
            "admission_date": "2026-04-01",
            "discharge_date": "2026-04-02",
            "diagnosis": [
                "Chronic Kidney Disease Stage 3b",
                "Renal Tubular Acidosis",
                "Secondary Hyperparathyroidism",
            ],
            "medications": [
                {"name": "Amlodipine", "dose": 5, "unit": "mg", "frequency": "Daily orally"},
                {"name": "Sodium Bicarbonate", "dose": 650, "unit": "mg", "frequency": "Twice daily orally"},
                {"name": "Calcitriol", "dose": 0.25, "unit": "mcg", "frequency": "Daily orally"},
            ],
            "summary": (
                "58-year-old male with stage 3b CKD admitted for 24-hour observation and electrolyte optimization. "
                "Serum creatinine stable at 1.8 mg/dL (baseline 1.7-1.9 mg/dL) with eGFR 44 mL/min/1.73m2. Serum potassium "
                "controlled at 4.6 mEq/L. Bicarbonate improved to 22 mEq/L on oral supplementation. Discharged with nephrology follow-up."
            ),
            "deliberate_errors": [],
            "extra_sections": [
                {
                    "title": "SERUM CHEMISTRY & RENAL PANEL RESULTS",
                    "table": {
                        "colWidths": [120, 80, 100, 180],
                        "data": [
                            [
                                Paragraph("Test Name", get_document_styles()["table_header"]),
                                Paragraph("Value", get_document_styles()["table_header"]),
                                Paragraph("Reference Range", get_document_styles()["table_header"]),
                                Paragraph("Interpretation", get_document_styles()["table_header"]),
                            ],
                            [
                                Paragraph("Serum Creatinine", get_document_styles()["table_cell"]),
                                Paragraph("1.8 mg/dL", get_document_styles()["table_cell"]),
                                Paragraph("0.7 - 1.3 mg/dL", get_document_styles()["table_cell"]),
                                Paragraph("Elevated; stable at chronic baseline", get_document_styles()["table_cell"]),
                            ],
                            [
                                Paragraph("Blood Urea Nitrogen", get_document_styles()["table_cell"]),
                                Paragraph("28 mg/dL", get_document_styles()["table_cell"]),
                                Paragraph("7 - 20 mg/dL", get_document_styles()["table_cell"]),
                                Paragraph("Mildly elevated secondary to CKD", get_document_styles()["table_cell"]),
                            ],
                            [
                                Paragraph("Serum Potassium", get_document_styles()["table_cell"]),
                                Paragraph("4.6 mEq/L", get_document_styles()["table_cell"]),
                                Paragraph("3.5 - 5.0 mEq/L", get_document_styles()["table_cell"]),
                                Paragraph("Within normal limits", get_document_styles()["table_cell"]),
                            ],
                            [
                                Paragraph("Serum Bicarbonate", get_document_styles()["table_cell"]),
                                Paragraph("22 mEq/L", get_document_styles()["table_cell"]),
                                Paragraph("22 - 29 mEq/L", get_document_styles()["table_cell"]),
                                Paragraph("Normalized on sodium bicarbonate", get_document_styles()["table_cell"]),
                            ],
                        ],
                    },
                }
            ],
        },
        # 8. Deliberate Error 4: Patient age out of range (age: 142 > 120)
        {
            "filename_stem": "lab_report_02_error_age",
            "report_title": "Laboratory & Diagnostic Clinical Report - Hematology",
            "patient": {"name": "Hannah Abbott", "age": 142, "sex": "F"},  # Deliberate Error: age 142 > 120
            "demographics": {
                "mrn": "MRN-2026-55912",
                "phone": "555-016-9934",
                "email": "hannah.a.fake@example-hospital.org",
            },
            "admission_date": "2026-04-10",
            "discharge_date": "2026-04-11",
            "diagnosis": [
                "Microcytic Hypochromic Iron Deficiency Anemia",
                "Fatigue",
            ],
            "medications": [
                {"name": "Ferrous Gluconate", "dose": 324, "unit": "mg", "frequency": "Daily orally with orange juice"},
                {"name": "Ascorbic Acid", "dose": 500, "unit": "mg", "frequency": "Daily orally"},
            ],
            "summary": (
                "Patient presenting for diagnostic evaluation of fatigue. Complete blood count demonstrated microcytic "
                "hypochromic anemia with hemoglobin 9.4 g/dL and MCV 72 fL. Serum ferritin markedly decreased at 8 ng/mL. "
                "Started on oral iron repletion and outpatient gastroenterology consult arranged."
            ),
            "deliberate_errors": [
                {
                    "field": "patient.age",
                    "rule": "age_between_0_and_120",
                    "severity": "error",
                    "message": "age between 0 and 120 (found age 142)",
                }
            ],
            "extra_sections": [
                {
                    "title": "HEMATOLOGY COMPLETE BLOOD COUNT RESULTS",
                    "table": {
                        "colWidths": [120, 80, 100, 180],
                        "data": [
                            [
                                Paragraph("Test Name", get_document_styles()["table_header"]),
                                Paragraph("Value", get_document_styles()["table_header"]),
                                Paragraph("Reference Range", get_document_styles()["table_header"]),
                                Paragraph("Interpretation", get_document_styles()["table_header"]),
                            ],
                            [
                                Paragraph("Hemoglobin", get_document_styles()["table_cell"]),
                                Paragraph("9.4 g/dL", get_document_styles()["table_cell"]),
                                Paragraph("12.0 - 16.0 g/dL", get_document_styles()["table_cell"]),
                                Paragraph("Decreased (Moderate Anemia)", get_document_styles()["table_cell"]),
                            ],
                            [
                                Paragraph("Mean Corpuscular Vol", get_document_styles()["table_cell"]),
                                Paragraph("72 fL", get_document_styles()["table_cell"]),
                                Paragraph("80 - 100 fL", get_document_styles()["table_cell"]),
                                Paragraph("Microcytosis", get_document_styles()["table_cell"]),
                            ],
                            [
                                Paragraph("Serum Ferritin", get_document_styles()["table_cell"]),
                                Paragraph("8 ng/mL", get_document_styles()["table_cell"]),
                                Paragraph("15 - 150 ng/mL", get_document_styles()["table_cell"]),
                                Paragraph("Severely depleted iron stores", get_document_styles()["table_cell"]),
                            ],
                        ],
                    },
                }
            ],
        },
    ]

    return reports


def generate_all_synthetic_data(output_dir: Path) -> Dict[str, Any]:
    """Generate all synthetic SOPs and clinical reports (PDF + ground-truth JSON)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_summary: Dict[str, Any] = {
        "sops": [],
        "reports": [],
        "ground_truth_json": [],
    }

    # 1. Generate 5 SOPs
    sops = [
        ("sop_infection_control.pdf", generate_sop_infection_control),
        ("sop_discharge_process.pdf", generate_sop_discharge_process),
        ("sop_billing_financial.pdf", generate_sop_billing_financial),
        ("sop_medication_safety.pdf", generate_sop_medication_safety),
        ("sop_patient_consent.pdf", generate_sop_patient_consent),
    ]

    print(f"Generating 5 Standard Operating Procedures in {output_dir}...")
    for filename, generator_func in sops:
        pdf_path = output_dir / filename
        generator_func(pdf_path)
        generated_summary["sops"].append(str(pdf_path))
        print(f"  [+] Created SOP: {filename}")

    # 2. Generate Clinical Reports & Ground-Truth JSONs
    reports = get_synthetic_reports_dataset()
    print(f"Generating {len(reports)} Clinical Reports & Ground-Truth JSONs in {output_dir}...")

    for rep in reports:
        stem = rep["filename_stem"]
        pdf_path = output_dir / f"{stem}.pdf"
        json_path = output_dir / f"{stem}.json"

        # Combine patient info with demographics for PDF rendering
        patient_render_data = dict(rep["patient"])
        patient_render_data.update(rep["demographics"])

        # Generate PDF
        generate_clinical_report_pdf(
            output_path=pdf_path,
            report_title=rep["report_title"],
            patient_data=patient_render_data,
            admission_date=rep["admission_date"],
            discharge_date=rep["discharge_date"],
            diagnosis_list=rep["diagnosis"],
            medications_list=rep["medications"],
            summary_text=rep["summary"],
            extra_sections=rep.get("extra_sections"),
            deliberate_error_note=None,
        )
        generated_summary["reports"].append(str(pdf_path))

        # Ground-truth JSON strictly conforming to SPEC.md section 6 extraction schema
        ground_truth: Dict[str, Any] = {
            "patient": rep["patient"],
            "diagnosis": rep["diagnosis"],
            "medications": rep["medications"],
            "admission_date": rep["admission_date"],
            "discharge_date": rep["discharge_date"],
            "summary": rep["summary"],
            "_metadata": {
                "report_title": rep["report_title"],
                "synthetic_demographics": rep["demographics"],
                "has_deliberate_errors": len(rep["deliberate_errors"]) > 0,
                "expected_validation_issues": rep["deliberate_errors"],
            },
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ground_truth, f, indent=2)

        generated_summary["ground_truth_json"].append(str(json_path))
        status_suffix = " (WITH DELIBERATE ERRORS)" if rep["deliberate_errors"] else ""
        print(f"  [+] Created Report & JSON: {stem}.pdf / .json{status_suffix}")

    total_pdfs = len(generated_summary["sops"]) + len(generated_summary["reports"])
    print(f"\n[DONE] Successfully generated {total_pdfs} PDFs and {len(generated_summary['ground_truth_json'])} ground-truth JSON files.")
    return generated_summary


def main() -> None:
    """CLI entrypoint for synthetic data generation."""
    parser = argparse.ArgumentParser(description="Generate synthetic medical documents and SOPs for MediDoc AI.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "generated",
        help="Target directory to write PDFs and JSONs (default: data/generated)",
    )
    args = parser.parse_args()
    generate_all_synthetic_data(args.output_dir)


if __name__ == "__main__":
    main()
