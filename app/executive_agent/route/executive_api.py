import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Body, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.common.document_utils import (
    docx_response,
    extract_text_from_file,
    normalize_report_payload,
    save_agent_upload,
    write_json_output,
)
from app.executive_agent import run_executive_pipeline_agno

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/executive-report", tags=["Executive Reporting"])


@router.post("/generate")
async def generate(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required.")

    file_ids = []
    document_parts = []
    source_files = []
    try:
        for file in files:
            file_id, path = await save_agent_upload(file, "executive")
            text = extract_text_from_file(path)
            file_ids.append(file_id)
            source_files.append({"file_id": file_id, "filename": file.filename, "text_chars": len(text)})
            document_parts.append(f"Source file: {file.filename}\n{text}")
            logger.info("Executive source prepared file_id=%s filename=%s text_chars=%s", file_id, file.filename, len(text))
        result = run_executive_pipeline_agno("\n\n--- next document ---\n\n".join(document_parts))
    except Exception as exc:
        logger.exception("Executive report generation failed")
        raise HTTPException(status_code=500, detail=f"Executive report generation failed: {exc}") from exc

    response = {
        "file_ids": file_ids,
        "source_files": source_files,
        **result,
    }
    write_json_output(file_ids[0], "executive-report", response)
    return JSONResponse(response)


@router.post("/download")
async def download(payload: Dict[str, Any] = Body(...)):
    filename = payload.get("filename") or "workflow-executive-report.docx"
    report_payload = normalize_report_payload(payload)
    return docx_response("Executive PMO Report", report_payload, filename)
