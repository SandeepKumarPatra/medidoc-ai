"""Clinical extraction validation engine for MediDoc AI.

Enforces business and clinical rules defined in SPEC.md Section 6:
- discharge_date must not be before admission_date (rule: discharge_date_before_admission)
- every medication has a dose and a unit (rules: medication_missing_dose, medication_missing_unit)
- diagnosis list is not empty (rule: diagnosis_empty)
- patient age between 0 and 120 (rule: age_between_0_and_120)

Returns structured validation issues containing: field, rule, severity, message.
Exact rule names and formats match expected_validation_issues in synthetic benchmarks.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Union

from pydantic import BaseModel, ConfigDict, Field

from backend.app.extraction.schema import ClinicalExtraction


class ValidationIssueSchema(BaseModel):
    """Structured clinical validation finding."""

    field: str = Field(..., description="Target field path that triggered the rule")
    rule: str = Field(..., description="Machine-readable rule identifier")
    severity: str = Field(default="error", description="Issue severity: error or warning")
    message: str = Field(..., description="Human-readable explanation of the validation failure")

    model_config = ConfigDict(extra="ignore")


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Safely parse an ISO date string (YYYY-MM-DD)."""
    if not date_str:
        return None
    try:
        return datetime.strptime(str(date_str).strip()[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def validate_extraction(
    data: Union[ClinicalExtraction, Dict[str, Any]],
) -> List[ValidationIssueSchema]:
    """Validate extracted clinical data against SPEC.md validation rules.

    Args:
        data: Either a ClinicalExtraction Pydantic instance or raw dict.

    Returns:
        List of ValidationIssueSchema instances flagging all rule violations.
    """
    if isinstance(data, ClinicalExtraction):
        raw = data.model_dump()
    elif isinstance(data, dict):
        raw = data
    else:
        raise TypeError(f"Expected ClinicalExtraction or dict, received {type(data)}")

    issues: List[ValidationIssueSchema] = []

    # 1. Rule: Patient age between 0 and 120 (rule: age_between_0_and_120)
    patient = raw.get("patient") or {}
    age = patient.get("age")
    if age is not None:
        try:
            age_val = int(age)
            if age_val < 0 or age_val > 120:
                issues.append(
                    ValidationIssueSchema(
                        field="patient.age",
                        rule="age_between_0_and_120",
                        severity="error",
                        message=f"age between 0 and 120 (found age {age_val})",
                    )
                )
        except (ValueError, TypeError):
            issues.append(
                ValidationIssueSchema(
                    field="patient.age",
                    rule="age_between_0_and_120",
                    severity="error",
                    message=f"age between 0 and 120 (invalid value {age})",
                )
            )

    # 2. Rule: Discharge date must not be before admission date (rule: discharge_date_before_admission)
    adm_str = raw.get("admission_date")
    dis_str = raw.get("discharge_date")
    adm_date = _parse_date(adm_str)
    dis_date = _parse_date(dis_str)

    if adm_date and dis_date:
        if dis_date < adm_date:
            issues.append(
                ValidationIssueSchema(
                    field="discharge_date",
                    rule="discharge_date_before_admission",
                    severity="error",
                    message=f"discharge_date ({dis_str}) must not be before admission_date ({adm_str})",
                )
            )

    # 3. Rule: Diagnosis list is not empty (rule: diagnosis_empty)
    diagnoses = raw.get("diagnosis")
    if diagnoses is None or len(diagnoses) == 0:
        issues.append(
            ValidationIssueSchema(
                field="diagnosis",
                rule="diagnosis_empty",
                severity="error",
                message=f"diagnosis list is not empty (found {len(diagnoses or [])} diagnoses)",
            )
        )

    # 4. Rule: Every medication has a dose and a unit (rules: medication_missing_dose, medication_missing_unit)
    medications = raw.get("medications") or []
    for idx, med in enumerate(medications):
        if isinstance(med, dict):
            med_name = med.get("name") or "Medication"
            med_dose = med.get("dose")
            med_unit = med.get("unit")
        else:
            med_name = getattr(med, "name", "Medication")
            med_dose = getattr(med, "dose", None)
            med_unit = getattr(med, "unit", None)

        if med_dose is None:
            issues.append(
                ValidationIssueSchema(
                    field=f"medications[{idx}].dose",
                    rule="medication_missing_dose",
                    severity="error",
                    message=f"every medication must have a dose and a unit ({med_name} dose is missing)",
                )
            )

        if med_unit is None or (isinstance(med_unit, str) and not med_unit.strip()):
            issues.append(
                ValidationIssueSchema(
                    field=f"medications[{idx}].unit",
                    rule="medication_missing_unit",
                    severity="error",
                    message=f"every medication must have a dose and a unit ({med_name} unit is empty)",
                )
            )

    return issues
