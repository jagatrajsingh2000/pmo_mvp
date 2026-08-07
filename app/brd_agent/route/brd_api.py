import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.brd_agent import run_brd_pipeline_agno
from app.common.document_utils import (
    docx_response,
    extract_text_from_file,
    normalize_report_payload,
    save_agent_upload,
    write_json_output,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/brd", tags=["BRD Generator"])


class BrdGenerateRequest(BaseModel):
    fields: Dict[str, Any] = Field(default_factory=dict)
    filename: Optional[str] = "workflow-brd.docx"


@router.post("/preview")
async def preview(file: UploadFile = File(...)):
    file_id, path = await save_agent_upload(file, "brd")
    logger.info("BRD preview upload saved file_id=%s path=%s", file_id, path)
    try:
        text = extract_text_from_file(path)
        result = run_brd_pipeline_agno(text, file.filename or "workflow-brd.docx")
    except Exception as exc:
        logger.exception("BRD preview failed file_id=%s", file_id)
        raise HTTPException(status_code=500, detail=f"BRD preview failed: {exc}") from exc
    response = {
        **result,
        "source": {"file_id": file_id, "filename": file.filename, "text_chars": len(text)},
    }
    write_json_output(file_id, "brd-preview", response)
    return JSONResponse(response)


@router.post("/generate")
async def generate(payload: BrdGenerateRequest):
    source_text = json.dumps(payload.fields, ensure_ascii=False, indent=2)
    logger.info("BRD generate starting fields=%s", sorted(payload.fields.keys()))
    try:
        result = run_brd_pipeline_agno(source_text, payload.filename or "workflow-brd.docx")
    except Exception as exc:
        logger.exception("BRD generate failed")
        raise HTTPException(status_code=500, detail=f"BRD generate failed: {exc}") from exc
    return docx_response("Business Requirements Document", result.get("resolved", result), payload.filename or "workflow-brd.docx")


@router.post("/download")
async def download(payload: Dict[str, Any] = Body(...)):
    filename = payload.get("filename") or payload.get("output_filename") or "workflow-brd.docx"
    report_payload = normalize_report_payload(payload)
    if not report_payload:
        raise HTTPException(status_code=400, detail="Content has no valid sections.")
    return docx_response("Business Requirements Document", report_payload, filename)
