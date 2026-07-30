# PMO Timeline Planner Agent (FastAPI)

Simple FastAPI service to accept project documents (PDF, XLSX, CSV, DOCX, TXT), extract text locally, and call Azure OpenAI to produce timeline artifacts (WBS, schedule, milestones, etc.).

Quick start

1. Create and activate a Python environment (recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set your Azure OpenAI values.

4. Run the app:

```bash
uvicorn app.main:app --reload --port 8000
```

Endpoints

- `GET /health` - basic health check
- `POST /upload` - multipart upload file field `file` — returns `ai_response` with timeline artifacts

Note: This is an initial prototype. Files are stored in `uploads/` and outputs in `outputs/`.

Planner agent
 - AI agent code is in `planner_agent/` separated from the FastAPI service.
 - `planner_agent` currently implements a generator and reviewer and calls Azure OpenAI.

Frontend
 - A simple React frontend (Vite) is in `frontend/`. To run:

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the backend at `http://localhost:8000`.

Tesseract OCR
 - For scanned PDFs, the backend uses `pytesseract` + `pdf2image` as a fallback OCR method.
 - You must install the Tesseract binary on your system. On macOS:

```bash
brew install tesseract
```

Langraph integration
 - The project includes a lightweight Langraph adapter at `planner_agent/langraph_adapter.py`.
 - To enable full Langraph orchestration, install the `langraph` package and adapt the adapter to your Langraph API:

```bash
pip install langraph
```

If `langraph` is not installed, the app falls back to the internal pipeline implementation.
