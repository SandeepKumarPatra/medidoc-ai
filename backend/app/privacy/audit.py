"""PII-Safe Audit Logging for MediDoc AI.

Records operational telemetry for clinical endpoints (/ask, /ingest, /extract, /validate).

CRITICAL PRIVACY RULE:
NEVER store question text, document text, prompts, answers, or extracted values.
The audit log records ONLY metadata: endpoint, document_id, count of masked PII items,
latency in milliseconds, and status.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional, Union

from sqlalchemy.orm import Session

from backend.app.db.models import AuditLog

logger = logging.getLogger(__name__)


def record_audit_log(
    db: Session,
    endpoint: str,
    document_id: Optional[Union[uuid.UUID, str]] = None,
    pii_items_masked: int = 0,
    latency_ms: float = 0.0,
    status: str = "success",
) -> AuditLog:
    """Record an audit log entry capturing operational metadata only.

    Args:
        db: SQLAlchemy database session.
        endpoint: API endpoint name (e.g. '/extract', '/validate', '/ask', '/ingest').
        document_id: Optional UUID of the associated document.
        pii_items_masked: Count of PII items redacted during processing.
        latency_ms: Total processing duration in milliseconds.
        status: Operation status ('success' or 'error').

    Returns:
        The persisted AuditLog instance.
    """
    doc_uuid: Optional[uuid.UUID] = None
    if document_id is not None:
        if isinstance(document_id, uuid.UUID):
            doc_uuid = document_id
        else:
            try:
                doc_uuid = uuid.UUID(str(document_id))
            except (ValueError, TypeError):
                doc_uuid = None

    audit_entry = AuditLog(
        endpoint=endpoint,
        document_id=doc_uuid,
        pii_items_masked=int(pii_items_masked),
        latency_ms=round(float(latency_ms), 2),
        status=status,
    )

    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)

    logger.info(
        "Audit log recorded: endpoint=%s doc_id=%s pii_masked=%d latency=%.2fms status=%s",
        endpoint,
        doc_uuid,
        pii_items_masked,
        latency_ms,
        status,
    )
    return audit_entry
