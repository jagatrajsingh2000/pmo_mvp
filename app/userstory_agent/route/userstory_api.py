import logging
from typing import Any, Dict

from fastapi import APIRouter, Body, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.common.document_utils import (
    docx_response,
    extract_text_from_file,
    normalize_report_payload,
    save_agent_upload,
    write_json_output,
)
from app.userstory_agent import run_userstory_pipeline_agno

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/userstory", tags=["User Story Agent"])


@router.post("/generate-file")
async def generate_file(file: UploadFile = File(...)):
    file_id, path = await save_agent_upload(file, "userstory")
    logger.info("User Story upload saved file_id=%s path=%s", file_id, path)
    try:
        text = extract_text_from_file(path)
        result = run_userstory_pipeline_agno(text)
    except Exception as exc:
        logger.exception("User Story generation failed file_id=%s", file_id)
        raise HTTPException(status_code=500, detail=f"User Story generation failed: {exc}") from exc
    response = {
        "file_id": file_id,
        "filename": file.filename,
        "source_text_chars": len(text),
        **result,
    }
    write_json_output(file_id, "userstory", response)
    return JSONResponse(response)


@router.post("/download")
async def download(payload: Dict[str, Any] = Body(...)):
    filename = payload.get("filename") or "workflow-user-stories.docx"
    report_payload = normalize_report_payload(payload)
    return docx_response("User Story Backlog", report_payload, filename)
