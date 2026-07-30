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

        sheets = pd.read_excel(str(path), sheet_name=None, engine="openpyxl")
        parts = []
        for sheet_name, df in sheets.items():
            parts.append(f"Sheet: {sheet_name}")
            parts.append(df.to_csv(index=False))
        return "\n".join(parts)
    except Exception:
        raise


def _extract_text_csv(path: Path) -> str:
    try:
        import pandas as pd

        df = pd.read_csv(str(path))
        return df.to_csv(index=False)
    except Exception:
        raise
