import os
from pathlib import Path
import aiofiles
from typing import Union


def _ensure_path(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


async def save_upload_file(upload_file, destination: Union[str, Path]):
    dest = Path(destination)
    _ensure_path(dest)
    async with aiofiles.open(dest, "wb") as out_file:
        content = await upload_file.read()
        await out_file.write(content)


def extract_text_from_file(path: Union[str, Path]) -> str:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_text_pdf(path)
    if suffix in (".docx", ".doc"):
        return _extract_text_docx(path)
    if suffix in (".xlsx", ".xls"):
        return _extract_text_excel(path)
    if suffix == ".csv":
        return _extract_text_csv(path)
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    # fallback: try reading as text
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_text_pdf(path: Path) -> str:
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(str(path))
        texts = []
        for p in reader.pages:
            try:
                texts.append(p.extract_text() or "")
            except Exception:
                continue
        combined = "\n".join(texts)
        # If extracted text is very small, try OCR fallback for scanned PDFs
        if len(combined.strip()) < 100:
            try:
                from pdf2image import convert_from_path
                import pytesseract
                from PIL import Image

                images = convert_from_path(str(path))
                ocr_texts = []
                for img in images:
                    try:
                        ocr_texts.append(pytesseract.image_to_string(img))
                    except Exception:
                        continue
                ocr_combined = "\n".join(ocr_texts)
                # prefer OCR if richer
                if len(ocr_combined.strip()) > len(combined):
                    return ocr_combined
            except Exception:
                # If pdf2image/pytesseract aren't available or fail, return what we have
                pass

        return combined
    except Exception as e:
        raise


def _extract_text_docx(path: Path) -> str:
    try:
        import docx

        doc = docx.Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n".join(paragraphs)
    except Exception:
        raise


def _extract_text_excel(path: Path) -> str:
    try:
        import pandas as pd

        df = pd.read_excel(str(path), engine="openpyxl")
        return df.to_csv(index=False)
    except Exception:
        raise


def _extract_text_csv(path: Path) -> str:
    try:
        import pandas as pd

        df = pd.read_csv(str(path))
        return df.to_csv(index=False)
    except Exception:
        raise


def agent_create_outputs(document_text: str):
    """Agent that creates the required timeline outputs from extracted document text."""
    prompt = (
        "You are a project timeline planner. Given the following project document content, "
        "extract and produce a JSON object with the following keys: wbs, project_schedule, "
        "sprint_plan, milestone_plan, critical_path, dependency_map, resource_allocation, "
        "timeline_risks, effort_estimation, schedule_optimizations. Use arrays or simple objects. "
        "Return only valid JSON. If a field cannot be determined, set it to null or an empty array.\n\n"
        f"Document content:\n\n{document_text[:8000]}"
    )

    resp = call_azure_openai(prompt)
    return resp


def agent_review_outputs(original_text: str, generated_outputs):
    """Agent that reviews generated outputs and suggests improvements.

    `generated_outputs` may be a dict or text wrapper returned from `call_azure_openai`.
    """
    import json

    gen_json = generated_outputs
    if isinstance(generated_outputs, dict) and "text" in generated_outputs and not (
        any(k in generated_outputs for k in ("wbs", "project_schedule"))
    ):
        # If previous call returned raw text, try to include it as string
        gen_json = generated_outputs

    prompt = (
        "You are a senior project manager reviewing the generated project timeline outputs. "
        "Given the original project document content and the generated outputs, produce a short JSON object with: "
        "- issues: list of problems or missing information, "
        "- suggestions: list of concrete improvements or data to collect, "
        "- confidence: low/medium/high.\n\n"
        f"Original document snippet:\n{original_text[:3000]}\n\n"
        f"Generated outputs:\n{json.dumps(gen_json, ensure_ascii=False) if not isinstance(gen_json, str) else str(gen_json)}"
    )

    resp = call_azure_openai(prompt)
    return resp
