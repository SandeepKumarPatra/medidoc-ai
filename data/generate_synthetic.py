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
import random
from typing import Any, Dict, List, Optional

# Ensure deterministic generation
random.seed(42)

try:
    from data.sop_data import SOP_DEFINITIONS, SOP_QUESTIONS
except ImportError:
    from sop_data import SOP_DEFINITIONS, SOP_QUESTIONS

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
# SOP GENERATORS (12 Multi-page Policies with Tables, 6-10 Pages Each)
# ============================================================================


def generate_sop_from_spec(sop_spec: Dict[str, Any], output_path: Path) -> None:
    """Generate a multi-page SOP PDF adhering to 6-10 pages from a structured specification."""
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

    # Page 1 Header block
    story.append(Paragraph(sop_spec["subtitle"], styles["subtitle"]))
    story.append(Paragraph(sop_spec["title"], styles["title"]))
    metadata_line = (
        f"<b>Document ID:</b> {sop_spec['doc_id']} | "
        f"<b>Effective Date:</b> {sop_spec['effective_date']} | "
        f"<b>Review Cycle:</b> {sop_spec['review_cycle']} | "
        f"<b>Department:</b> {sop_spec['department']}"
    )
    story.append(Paragraph(metadata_line, styles["body"]))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#2B6CB0"),
            spaceBefore=3,
            spaceAfter=8,
        )
    )

    pages = sop_spec["pages"]
    num_pages = len(pages)

    for p_idx, page_blocks in enumerate(pages):
        for block in page_blocks:
            b_type = block.get("type")
            if b_type == "section":
                heading_text = block.get("heading", "")
                story.append(Paragraph(heading_text, styles["h1"]))
                for para in block.get("content", []):
                    story.append(Paragraph(para, styles["body"]))
            elif b_type == "table":
                col_widths = block.get("col_widths", [100, 100, 100, 100, 100])
                header_cells = [
                    Paragraph(h, styles["table_header"]) for h in block.get("header", [])
                ]
                table_rows = [header_cells]
                for row in block.get("rows", []):
                    table_rows.append([
                        Paragraph(cell, styles["table_cell"]) for cell in row
                    ])
                t = Table(table_rows, colWidths=col_widths)
                t.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#2B6CB0")),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7FAFC"), colors.white]),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ]
                    )
                )
                story.append(Spacer(1, 3))
                story.append(t)
                story.append(Spacer(1, 4))

        if p_idx < num_pages - 1:
            story.append(PageBreak())

    doc.build(story, canvasmaker=NumberedCanvas)


def generate_sop_infection_control(output_path: Path) -> None:
    """Generate multi-page SOP for Infection Control with isolation categories table."""
    generate_sop_from_spec(SOP_DEFINITIONS["infection_control"], output_path)


def generate_sop_discharge_process(output_path: Path) -> None:
    """Generate multi-page SOP for Inpatient Discharge Planning and Transitions."""
    generate_sop_from_spec(SOP_DEFINITIONS["discharge_process"], output_path)


def generate_sop_billing_financial(output_path: Path) -> None:
    """Generate multi-page SOP for Hospital Billing Compliance and Charge Capture."""
    generate_sop_from_spec(SOP_DEFINITIONS["billing_financial"], output_path)


def generate_sop_medication_safety(output_path: Path) -> None:
    """Generate multi-page SOP for High-Alert Medication Safety and Infusion Controls."""
    generate_sop_from_spec(SOP_DEFINITIONS["medication_safety"], output_path)


def generate_sop_patient_consent(output_path: Path) -> None:
    """Generate multi-page SOP for Informed Consent for Clinical Procedures."""
    generate_sop_from_spec(SOP_DEFINITIONS["patient_consent"], output_path)


def generate_sop_hand_hygiene(output_path: Path) -> None:
    """Generate multi-page SOP for Hand Hygiene Protocols and Sanitization Benchmarks."""
    generate_sop_from_spec(SOP_DEFINITIONS["hand_hygiene"], output_path)


def generate_sop_fall_prevention(output_path: Path) -> None:
    """Generate multi-page SOP for Inpatient Fall Risk Assessment and Post-Fall Protocol."""
    generate_sop_from_spec(SOP_DEFINITIONS["fall_prevention"], output_path)


def generate_sop_blood_transfusion(output_path: Path) -> None:
    """Generate multi-page SOP for Blood Component Transfusion and Adverse Reaction Management."""
    generate_sop_from_spec(SOP_DEFINITIONS["blood_transfusion"], output_path)


def generate_sop_emergency_code_response(output_path: Path) -> None:
    """Generate multi-page SOP for Hospital-Wide Emergency Codes and Resuscitation Protocols."""
    generate_sop_from_spec(SOP_DEFINITIONS["emergency_code_response"], output_path)


def generate_sop_patient_identification(output_path: Path) -> None:
    """Generate multi-page SOP for Two-Identifier Patient Identification and Wristband Standards."""
    generate_sop_from_spec(SOP_DEFINITIONS["patient_identification"], output_path)


def generate_sop_biomedical_waste(output_path: Path) -> None:
    """Generate multi-page SOP for Biomedical and Hazardous Waste Segregation and Disposal."""
    generate_sop_from_spec(SOP_DEFINITIONS["biomedical_waste"], output_path)


def generate_sop_pharmacy_storage(output_path: Path) -> None:
    """Generate multi-page SOP for Pharmaceutical Cold Chain Management and Inventory Storage."""
    generate_sop_from_spec(SOP_DEFINITIONS["pharmacy_storage"], output_path)


def generate_sop_questions_file(eval_dir: Path) -> Path:
    """Generate evaluation question set for all 12 SOPs in data/eval/sop_questions.json."""
    eval_dir.mkdir(parents=True, exist_ok=True)
    target_path = eval_dir / "sop_questions.json"
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(SOP_QUESTIONS, f, indent=2)
    return target_path


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
                "ambulating independently, pain controlled on oral analgesics."
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


def generate_all_synthetic_data(
    output_dir: Path,
    eval_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Generate all synthetic SOPs and clinical reports (PDF + ground-truth JSON)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if eval_dir is None:
        eval_dir = output_dir.parent / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)

    generated_summary: Dict[str, Any] = {
        "sops": [],
        "reports": [],
        "ground_truth_json": [],
        "sop_questions": None,
    }

    # 1. Generate 12 SOPs
    sops = [
        ("sop_infection_control.pdf", generate_sop_infection_control),
        ("sop_discharge_process.pdf", generate_sop_discharge_process),
        ("sop_billing_financial.pdf", generate_sop_billing_financial),
        ("sop_medication_safety.pdf", generate_sop_medication_safety),
        ("sop_patient_consent.pdf", generate_sop_patient_consent),
        ("sop_hand_hygiene.pdf", generate_sop_hand_hygiene),
        ("sop_fall_prevention.pdf", generate_sop_fall_prevention),
        ("sop_blood_transfusion.pdf", generate_sop_blood_transfusion),
        ("sop_emergency_code_response.pdf", generate_sop_emergency_code_response),
        ("sop_patient_identification.pdf", generate_sop_patient_identification),
        ("sop_biomedical_waste.pdf", generate_sop_biomedical_waste),
        ("sop_pharmacy_storage.pdf", generate_sop_pharmacy_storage),
    ]

    print(f"Generating 12 Standard Operating Procedures in {output_dir}...")
    for filename, generator_func in sops:
        pdf_path = output_dir / filename
        generator_func(pdf_path)
        generated_summary["sops"].append(str(pdf_path))
        print(f"  [+] Created SOP: {filename}")

    # 2. Generate Evaluation Questions File
    questions_path = generate_sop_questions_file(eval_dir)
    generated_summary["sop_questions"] = str(questions_path)
    print(f"  [+] Created SOP Evaluation Questions: {questions_path}")

    # 3. Generate Clinical Reports & Ground-Truth JSONs
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
    print(f"\n[DONE] Successfully generated {total_pdfs} PDFs, {len(generated_summary['ground_truth_json'])} ground-truth JSON files, and 1 SOP evaluation dataset.")
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
    parser.add_argument(
        "--eval-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "eval",
        help="Target directory to write evaluation question sets (default: data/eval)",
    )
    args = parser.parse_args()
    generate_all_synthetic_data(output_dir=args.output_dir, eval_dir=args.eval_dir)


if __name__ == "__main__":
    main()
