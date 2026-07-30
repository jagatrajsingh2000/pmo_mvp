from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
from pathlib import Path
from app.utils import save_upload_file, extract_text_from_file
from planner_agent import run_pipeline_langraph
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="PMO Timeline Planner Agent")

# Allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    dest = UPLOAD_DIR / filename
    try:
        await save_upload_file(file, dest)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to save upload: {e}")

    try:
        text = extract_text_from_file(dest)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"extract error: {e}")

    # Run the planner agent pipeline (generator + reviewer)
    try:
        generated, review = run_pipeline_langraph(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"pipeline error: {e}")

    out = {
        "file_id": file_id,
        "filename": filename,
        "extracted_text_snippet": text[:2000],
        "generated": generated,
        "review": review,
    }

    # Save output
    import json

    out_path = OUTPUT_DIR / f"{file_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    return JSONResponse(out)
