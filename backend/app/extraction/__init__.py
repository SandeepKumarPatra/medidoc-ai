"""Clinical document extraction and validation package."""

from backend.app.extraction.extractor import ExtractionResult, extract_clinical_document
from backend.app.extraction.schema import ClinicalExtraction, MedicationItem, PatientInfo
from backend.app.extraction.validator import ValidationIssueSchema, validate_extraction

__all__ = [
    "ClinicalExtraction",
    "MedicationItem",
    "PatientInfo",
    "ValidationIssueSchema",
    "validate_extraction",
    "extract_clinical_document",
    "ExtractionResult",
]
