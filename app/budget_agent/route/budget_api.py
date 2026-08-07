import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, Body, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.budget_agent import run_budget_pipeline_agno
from app.common.document_utils import (
    docx_response,
    extract_text_from_file,
    normalize_report_payload,
    save_agent_upload,
    write_json_output,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/budget", tags=["Budget Agent"])


@router.post("/generate-from-file")
async def generate_from_file(file: UploadFile = File(...)):
    file_id, path = await save_agent_upload(file, "budget")
    logger.info("Budget upload saved file_id=%s path=%s", file_id, path)
    try:
        text = extract_text_from_file(path)
        result = run_budget_pipeline_agno(text)
    except Exception as exc:
        logger.exception("Budget generation failed file_id=%s", file_id)
        raise HTTPException(status_code=500, detail=f"Budget generation failed: {exc}") from exc
    response = {
        "file_id": file_id,
        "filename": file.filename,
        "source_text_chars": len(text),
        **result,
    }
    write_json_output(file_id, "budget", response)
    return JSONResponse(response)


@router.post("/generate")
async def generate(payload: Dict[str, Any] = Body(...)):
    logger.info("Budget generate starting payload_keys=%s", sorted(payload.keys()))
    try:
        result = run_budget_pipeline_agno(json.dumps(payload, ensure_ascii=False, indent=2))
    except Exception as exc:
        logger.exception("Budget generate failed")
        raise HTTPException(status_code=500, detail=f"Budget generation failed: {exc}") from exc
    return JSONResponse(result)


@router.post("/download")
async def download(payload: Dict[str, Any] = Body(...)):
    filename = payload.get("filename") or "workflow-budget.docx"
    report_payload = normalize_report_payload(payload)
    return docx_response("Project Budget Report", report_payload, filename)
