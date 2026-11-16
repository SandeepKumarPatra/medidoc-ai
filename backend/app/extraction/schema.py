"""Pydantic extraction schema for MediDoc AI.

Conforms to SPEC.md Section 6:
- patient: {name: str, age: int, sex: M|F|O}
- diagnosis: list[str]
- medications: list[{name: str, dose: float|null, unit: str|null, frequency: str}]
- admission_date: YYYY-MM-DD
- discharge_date: YYYY-MM-DD
- summary: clinician-style summary

Dosage and unit are optional so that missing values parse as null/None
and are flagged by the validator rather than rejected by the schema.
"""

from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class PatientInfo(BaseModel):
    """Patient demographic details."""

    name: str = Field(..., description="Patient full name or masked token (e.g. [NAME])")
    age: int = Field(..., description="Patient age in years")
    sex: Literal["M", "F", "O"] = Field(..., description="Biological sex: M, F, or O")

    model_config = ConfigDict(extra="ignore")


class MedicationItem(BaseModel):
    """Clinical medication entry with optional dosage and unit."""

    name: str = Field(..., description="Medication brand or generic name")
    dose: Optional[float] = Field(
        default=None,
        description="Dosage numeric quantity (null if missing or unspecified)",
    )
    unit: Optional[str] = Field(
        default=None,
        description="Dosage measurement unit, e.g. mg, mcg, mL, capsule (null if missing)",
    )
    frequency: Optional[str] = Field(
        default="",
        description="Dosage administration frequency and route instructions",
    )

    model_config = ConfigDict(extra="ignore")


class ClinicalExtraction(BaseModel):
    """Structured clinical discharge summary or lab report extraction."""

    patient: PatientInfo = Field(..., description="Patient demographic information")
    diagnosis: List[str] = Field(
        default_factory=list,
        description="Primary and secondary diagnosis list",
    )
    medications: List[MedicationItem] = Field(
        default_factory=list,
        description="Prescribed medications list",
    )
    admission_date: str = Field(
        ...,
        description="Hospital admission or encounter start date (YYYY-MM-DD)",
    )
    discharge_date: str = Field(
        ...,
        description="Hospital discharge or encounter end date (YYYY-MM-DD)",
    )
    summary: str = Field(
        ...,
        description="Concise clinician-style hospital course or laboratory summary",
    )

    model_config = ConfigDict(extra="ignore")
