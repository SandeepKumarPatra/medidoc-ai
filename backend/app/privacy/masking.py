"""PII Masking Engine for MediDoc AI.

Identifies and masks Protected Health Information (PHI) and Personally Identifiable
Information (PII) before documents or text are sent to LLMs.

Rules:
- Labelled fields (e.g., "Patient Name:", "MRN:", "Contact:", "Patient Email:", "Attending:")
- Pattern-based regex for names, phone numbers, email addresses, MRN, and ID-like numbers.
- Replacement tokens: [NAME], [PHONE], [EMAIL], [MRN].
- Strictly preserves clinical values: ages, dates, diagnoses, medication names, and doses.
- Returns masked text and counts per PII type (never returns or logs original values).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Set, Tuple


@dataclass
class MaskingResult:
    """Result of PII masking containing masked text and redacted item statistics."""

    masked_text: str
    pii_counts: Dict[str, int] = field(default_factory=dict)
    total_masked: int = 0

    def __iter__(self) -> Iterator[object]:
        """Support tuple unpacking: masked_text, counts = mask_pii(text)."""
        return iter((self.masked_text, self.pii_counts))


# --- Regex Patterns ---

EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# Standard 10-digit North American phone numbers and variations (e.g. 555-014-9821, (555) 014-9821, +1 555-014-9821)
PHONE_REGEX = re.compile(
    r"(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?[2-9]\d{2}[-.\s]?\d{4}\b"
)

# MRN pattern (e.g., MRN-2026-89102, MRN: 12345, MRN#98765)
MRN_REGEX = re.compile(
    r"\bMRN(?:-|\s*#?\s*)[A-Za-z0-9-]+\b",
    re.IGNORECASE,
)

# National / Regional ID patterns (Aadhaar-like 12 digits, PAN-like 10 chars, SSN-like 9 digits)
ID_PATTERNS = [
    # Aadhaar-like (4 4 4 digits)
    re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b"),
    # PAN-like (5 letters, 4 digits, 1 letter)
    re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    # SSN-like (3-2-4 digits)
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
]

# Clinician title pattern (e.g., Dr. Sharon Patel, MD, FACP or Dr. S. Patel, MD)
DOCTOR_NAME_REGEX = re.compile(
    r"\bDr\.\s+[A-Z][a-zA-Z]*(?:\s+[A-Z]\.?)*(?:\s+[A-Za-z-]+)+(?:,\s*(?:MD|DO|MBBS|FACP|PhD))?",
)

# Labelled field regexes (handles plain text, bold markdown, or HTML tags)
# Group 1 = Label prefix (e.g. 'Patient Name:'), Group 2 = Value to redact
LABELLED_PATIENT_NAME_REGEX = re.compile(
    r"((?:<b>|\*\*|#+)?\s*(?:Patient\s+Name|Patient)\s*:\s*(?:</b>|\*\*)?\s*)"
    r"([A-Za-z\s.'-]+?)"
    r"(?=\s*(?:<|\||\bMRN\b|\bAge\b|\bAdmission\b|\bContact\b|\bDischarge\b|\bFacility\b|\bEmail\b|\bPhone\b|\bPRIMARY\b|\bDISCHARGE\b|\bHOSPITAL\b|$))",
    re.IGNORECASE,
)

LABELLED_ATTENDING_NAME_REGEX = re.compile(
    r"((?:<b>|\*\*|#+)?\s*(?:Attending\s+Clinician|Attending|Physician|Doctor)\s*:\s*(?:</b>|\*\*)?\s*)"
    r"((?:Dr\.\s+)?[A-Za-z\s.,'-]+?)"
    r"(?=\s*(?:<|\||\(Synthetic\)|\bElectronic\b|\bDate\b|\bFacility\b|\bPRIMARY\b|\bDISCHARGE\b|\bHOSPITAL\b|$))",
    re.IGNORECASE,
)

LABELLED_MRN_REGEX = re.compile(
    r"((?:<b>|\*\*|#+)?\s*(?:MRN|Medical\s+Record\s+Number)\s*:\s*(?:</b>|\*\*)?)"
    r"([A-Za-z0-9#-]+)",
    re.IGNORECASE,
)

LABELLED_PHONE_REGEX = re.compile(
    r"((?:<b>|\*\*|#+)?\s*(?:Contact|Phone|Telephone|Tel|Mobile|Cell)\s*:\s*(?:</b>|\*\*)?)"
    r"([+\d\s().-]{7,25})",
    re.IGNORECASE,
)

LABELLED_EMAIL_REGEX = re.compile(
    r"((?:<b>|\*\*|#+)?\s*(?:Patient\s+Email|Email|E-mail)\s*:\s*(?:</b>|\*\*)?\s*)"
    r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})",
    re.IGNORECASE,
)


def mask_pii(text: str) -> MaskingResult:
    """Mask PII/PHI in clinical text using labelled rules and regex patterns.

    Args:
        text: Raw document text to mask.

    Returns:
        MaskingResult with masked_text, pii_counts by type, and total_masked.
    """
    if not text:
        return MaskingResult(masked_text="", pii_counts={}, total_masked=0)

    pii_counts: Dict[str, int] = {
        "NAME": 0,
        "PHONE": 0,
        "EMAIL": 0,
        "MRN": 0,
    }

    masked = text
    extracted_names: Set[str] = set()

    # 1. Labelled Email (preserve label, replace email value)
    def _sub_labelled_email(match: re.Match) -> str:
        prefix = match.group(1)
        pii_counts["EMAIL"] += 1
        return f"{prefix}[EMAIL]"

    masked = LABELLED_EMAIL_REGEX.sub(_sub_labelled_email, masked)

    # 2. Standalone Email addresses
    def _sub_email(match: re.Match) -> str:
        pii_counts["EMAIL"] += 1
        return "[EMAIL]"

    masked = EMAIL_REGEX.sub(_sub_email, masked)

    # 3. Labelled Phone / Contact
    def _sub_labelled_phone(match: re.Match) -> str:
        prefix = match.group(1)
        pii_counts["PHONE"] += 1
        return f"{prefix}[PHONE]"

    masked = LABELLED_PHONE_REGEX.sub(_sub_labelled_phone, masked)

    # 4. Standalone Phone numbers
    def _sub_phone(match: re.Match) -> str:
        pii_counts["PHONE"] += 1
        return "[PHONE]"

    masked = PHONE_REGEX.sub(_sub_phone, masked)

    # 5. Labelled MRN
    def _sub_labelled_mrn(match: re.Match) -> str:
        prefix = match.group(1)
        pii_counts["MRN"] += 1
        return f"{prefix}[MRN]"

    masked = LABELLED_MRN_REGEX.sub(_sub_labelled_mrn, masked)

    # 6. Standalone MRN
    def _sub_mrn(match: re.Match) -> str:
        pii_counts["MRN"] += 1
        return "[MRN]"

    masked = MRN_REGEX.sub(_sub_mrn, masked)

    # 7. Other ID patterns (Aadhaar, PAN, SSN)
    for id_pat in ID_PATTERNS:
        def _sub_id(match: re.Match) -> str:
            pii_counts["MRN"] += 1
            return "[MRN]"

        masked = id_pat.sub(_sub_id, masked)

    # 8. Labelled Patient Name
    def _sub_labelled_patient_name(match: re.Match) -> str:
        prefix = match.group(1)
        name_val = match.group(2).strip()
        if name_val and name_val != "[NAME]":
            extracted_names.add(name_val)
            normalized = " ".join(name_val.split())
            extracted_names.add(normalized)
            for part in normalized.split():
                if len(part) >= 3 and part.lower() not in {"and", "the", "for", "with", "patient", "name"}:
                    extracted_names.add(part)
            pii_counts["NAME"] += 1
            return f"{prefix}[NAME]\n"
        return match.group(0)

    masked = LABELLED_PATIENT_NAME_REGEX.sub(_sub_labelled_patient_name, masked)

    # 9. Labelled Attending / Doctor Name
    def _sub_labelled_attending(match: re.Match) -> str:
        prefix = match.group(1)
        name_val = match.group(2).strip()
        if name_val and name_val != "[NAME]":
            extracted_names.add(name_val)
            normalized = " ".join(name_val.split())
            extracted_names.add(normalized)
            for part in normalized.split():
                if len(part) >= 3 and part.lower() not in {"and", "the", "for", "with", "attending", "doctor", "clinician"}:
                    extracted_names.add(part)
            pii_counts["NAME"] += 1
            return f"{prefix}[NAME] "
        return match.group(0)

    masked = LABELLED_ATTENDING_NAME_REGEX.sub(_sub_labelled_attending, masked)

    # 10. Clinician Titles (e.g. Dr. Sharon Patel, MD, FACP)
    def _sub_doctor(match: re.Match) -> str:
        pii_counts["NAME"] += 1
        return "[NAME]"

    masked = DOCTOR_NAME_REGEX.sub(_sub_doctor, masked)

    # 11. Propagate identified patient names and components across free text
    for name in sorted(extracted_names, key=len, reverse=True):
        cleaned_name = name.strip()
        if len(cleaned_name) >= 3 and cleaned_name not in {"[NAME]", "[PHONE]", "[EMAIL]", "[MRN]"}:
            name_pattern = re.compile(r"\b" + re.escape(cleaned_name) + r"\b", re.IGNORECASE)
            matches = list(name_pattern.finditer(masked))
            if matches:
                pii_counts["NAME"] += len(matches)
                masked = name_pattern.sub("[NAME]", masked)

    total_masked = sum(pii_counts.values())

    return MaskingResult(
        masked_text=masked,
        pii_counts=pii_counts,
        total_masked=total_masked,
    )
