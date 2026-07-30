import json
import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.utils import save_upload_file, extract_text_from_file
from planner_agent import run_pipeline_langraph
from planner_agent.azure_client import planner_status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="PMO Timeline Planner Agent")

# Allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/planner-status")
def get_planner_status():
    status = planner_status()
    logger.info("Planner status requested status=%s", status)
    return status


def _build_response(file_id: str, filename: str, text: str):
    logger.info("Pipeline starting file_id=%s filename=%s text_chars=%s", file_id, filename, len(text))
    generated, review = run_pipeline_langraph(text)
    response = {
        "file_id": file_id,
        "filename": filename,
        "extracted_text_snippet": text[:2000],
        "generated": generated,
        "review": review,
    }
    logger.info("Pipeline completed file_id=%s generated_keys=%s", file_id, sorted(generated.keys()))
    return response


def _save_output(file_id: str, output: dict) -> None:
    out_path = OUTPUT_DIR / f"{file_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    logger.info("Output saved file_id=%s path=%s", file_id, out_path)


@app.get("/sample-documents")
def sample_documents():
    sample_dir = BASE_DIR / "sample_docs"
    documents = []
    if sample_dir.exists():
        for path in sorted(sample_dir.iterdir()):
            if path.is_file():
                documents.append({"filename": path.name, "path": str(path.relative_to(BASE_DIR))})
    return {"documents": documents}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    dest = UPLOAD_DIR / filename
    logger.info("Upload received file_id=%s original_filename=%s content_type=%s", file_id, file.filename, file.content_type)
    try:
        await save_upload_file(file, dest)
    except Exception as e:
        logger.exception("Upload save failed file_id=%s destination=%s", file_id, dest)
        raise HTTPException(status_code=500, detail=f"failed to save upload: {e}")
    logger.info("Upload saved file_id=%s path=%s", file_id, dest)

    try:
        text = extract_text_from_file(dest)
    except Exception as e:
        logger.exception("Text extraction failed file_id=%s path=%s", file_id, dest)
        raise HTTPException(status_code=500, detail=f"extract error: {e}")
    logger.info("Text extraction completed file_id=%s text_chars=%s", file_id, len(text))

    try:
        out = _build_response(file_id, filename, text)
    except Exception as e:
        logger.exception("Planner pipeline failed file_id=%s", file_id)
        raise HTTPException(status_code=500, detail=f"pipeline error: {e}")

    _save_output(file_id, out)
    return JSONResponse(out)


@app.post("/plan-text")
async def plan_text(payload: dict):
    text = str(payload.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    file_id = str(uuid.uuid4())
    logger.info("Direct text planning received file_id=%s text_chars=%s", file_id, len(text))
    out = _build_response(file_id, "direct_text_input.txt", text)
    _save_output(file_id, out)
    return JSONResponse(out)
