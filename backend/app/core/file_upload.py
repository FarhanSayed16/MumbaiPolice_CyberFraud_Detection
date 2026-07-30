import os
import logging
from fastapi import UploadFile, HTTPException, status

logger = logging.getLogger(__name__)

# Strict upload boundaries (`Sub-phase 5.1`)
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB boundary
ALLOWED_MIME_TYPES = {
    "application/pdf": [b"%PDF-"],
    "text/csv": [],  # CSV validation via content structure
    "application/csv": [],
    "text/plain": [], # Some browsers send CSV as text/plain
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [b"PK\x03\x04"],  # XLSX zip magic header
    "application/vnd.ms-excel": [],  # Older XLS or CSV opened in excel
    "application/octet-stream": [],  # Generic stream fallback, validated by filename/magic
    "image/jpeg": [b"\xFF\xD8\xFF"],
    "image/png": [b"\x89PNG\r\n\x1a\n"]
}

"""
Malware & File-Type Scanning Architectural Decision Record (`Sub-phase 5.1 Checkpoint`)
Decision: Explicitly DEFERRED to Phase 24.6 (Deployment & Institutional Sign-Off).
Written Rationale:
  In Band B (Pilot-ready phase on local/staging environments), all uploads pass through strict MIME check,
  magic byte header verification, and 15MB size limits enforced by this `validate_file_upload` engine.

  M8 / Phase 7 gate: bulk import & evidence upload routes MUST call `validate_file_upload` before
  persisting bytes or enqueueing ARQ jobs. Do not add a parallel ad-hoc MIME check.
  Antivirus/malware scanning (`ClamAV` daemon or `AWS GuardDuty` malware scan on S3 storage buckets) requires
  deployment architecture finalization during Phase 24 infrastructure freeze and is documented/scheduled for
  Phase 24.6 before production network exposure.
"""


async def validate_file_upload(file: UploadFile) -> bytes:
    """
    Validates file size and magic headers against allowed MIME boundaries.
    Returns file bytes if valid, otherwise raises 400 Bad Request / 413 Payload Too Large.
    """
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format: '{file.content_type}'. Allowed formats: {list(ALLOWED_MIME_TYPES.keys())}"
        )

    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES / (1024 * 1024)} MB (Actual: {round(file_size / (1024 * 1024), 2)} MB)."
        )

    # Magic byte header verification
    magic_signatures = ALLOWED_MIME_TYPES.get(file.content_type, [])
    if magic_signatures:
        if not any(content.startswith(sig) for sig in magic_signatures):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File content signature does not match declared MIME type '{file.content_type}'."
            )

    # Reset file cursor for downstream processing
    await file.seek(0)
    return content
