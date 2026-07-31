# PMO Timeline Planner Agent (FastAPI)

FastAPI + React app that accepts project documents (PDF, XLSX, CSV, DOCX, TXT), extracts text locally, and generates PMO timeline artifacts: WBS, project schedule, sprint plan, milestone plan, critical path, dependency map, resource allocation, timeline risks, effort estimates, and schedule optimization recommendations.

The planner uses Azure OpenAI through the official OpenAI Python SDK. Azure OpenAI configuration is required for all planner artifact generation.

Quick Start

Use a project-local Python virtual environment for the backend. The `.venv/` folder is ignored by git.

macOS / Linux backend

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Windows backend

PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Command Prompt:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

If Windows blocks PowerShell activation, run this once in PowerShell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate the environment again.

Configure Azure OpenAI values in `.env` for AI-generated plans:

```bash
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-PREVIEW
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

Missing Azure values, Azure API errors, invalid JSON, or incomplete planner artifacts fail clearly instead of silently using local output.

Endpoints

- `GET /health` - basic health check
- `GET /planner-status` - shows whether Azure OpenAI is configured, without exposing secrets
- `GET /sample-documents` - lists local documents under `sample_docs/`
- `POST /upload` - multipart upload file field `file`; returns generated planner artifacts and review
- `POST /plan-text` - JSON body with `text`; returns generated planner artifacts and review

Note: This is an initial prototype. Files are stored in `uploads/` and outputs in `outputs/`.

Planner agent
 - FastAPI planner routes live in `app/planner_agent/route/planer_api.py`.
 - Upload saving and document text extraction helpers live in `app/planner_agent/route/utils.py`.
 - Azure OpenAI and LangGraph agent code lives in `app/planner_agent/agent/`.
 - Shared prompt contracts live in `app/planner_agent/agent/prompts.py` to keep generation and review DRY.

Frontend
 - A React frontend (Vite) is in `frontend/`. Run it in a second terminal while the backend is running.
 - The report includes visual charts for schedule, milestones, dependencies, resources, effort, and risks.
 - The generated output has a separate `Quality Scores` tab for input grounding, business accuracy, requirements quality, hallucination control, traceability, stakeholder mapping, risk management, technical accuracy, BRD completeness, and audit readiness.
 - Use the `Export PDF` button after generation. It opens the browser print dialog; choose `Save as PDF` or `Microsoft Print to PDF`.

macOS / Linux:

```bash
cd frontend
npm install
npm run dev
```

Windows PowerShell or Command Prompt:

```powershell
cd frontend
npm install
npm run dev
```

Open the frontend at `http://localhost:5173`. It expects the backend at `http://localhost:8000`.

Stopping Servers And Port Conflicts

Usually, press `Ctrl+C` in the terminal where the backend or frontend is running.

If the backend fails with `Address already in use` on port `8000`, stop the process using that port.

macOS / Linux:

```bash
lsof -ti :8000
kill -9 $(lsof -ti :8000)
```

Windows PowerShell:

```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

If the frontend port `5173` is already in use, stop the process using that port.

macOS / Linux:

```bash
lsof -ti :5173
kill -9 $(lsof -ti :5173)
```

Windows PowerShell:

```powershell
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

Only use these broad commands when you intentionally want to stop every running Python or Node process.

macOS / Linux:

```bash
pkill -f python
pkill -f node
```

Windows PowerShell:

```powershell
taskkill /IM python.exe /F
taskkill /IM node.exe /F
```

Sample documents
 - Test inputs are in `sample_docs/`.
 - Start with `sample_docs/pmo_timeline_brd_sample.txt` for the most complete PMO timeline example.

Tesseract OCR
 - For scanned PDFs, the backend can use `pytesseract` + `pdf2image` to extract text from page images.
 - You must install the Tesseract binary on your system. On macOS:

```bash
brew install tesseract
```

LangGraph integration
 - The project includes a LangGraph adapter at `app/planner_agent/agent/langraph_adapter.py`.
 - You do not start LangGraph as a separate server. Start the FastAPI backend; the backend runs the LangGraph planner pipeline inside the Python process.
 - `langgraph` is included in `requirements.txt`, so it is installed when you install backend dependencies in `.venv`.
 - To start the backend with LangGraph available:

macOS / Linux:

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

If `langgraph` is not installed, the backend fails clearly instead of running a partial planner pipeline. Azure OpenAI is required.

Check OpenAI Usage
 - Start the backend and call:

```bash
curl http://localhost:8000/planner-status
```

Expected when Azure OpenAI is configured:

```json
{
  "azure_openai_configured": true,
  "provider": "azure_openai"
}
```

Debug Upload Failures
 - Watch the backend terminal where `uvicorn` is running. The app logs each stage:
   - upload received
   - upload saved
   - text extraction completed
   - LangGraph pipeline started
   - generate node started/completed
   - Azure OpenAI request started/completed
   - review node started/completed
   - output saved
 - If upload fails, the frontend shows the backend error message in an `Upload Failed` panel.
 - The upload fails if Azure OpenAI is not configured, Azure returns an error, LangGraph is unavailable, or the AI response does not include all required planner artifact keys.
 - Generator requests use Azure OpenAI JSON mode with `response_format={"type":"json_object"}`.
 - If the first AI response is invalid JSON or misses required artifact keys, the generator makes one stricter AI repair request. If that also fails, the upload fails instead of rendering incomplete data.
