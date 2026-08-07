# PMO Multi-Agent Workflow API (FastAPI)

FastAPI + React app that accepts project documents (PDF, XLSX, CSV, DOCX, TXT), extracts text locally, and runs a PMO workflow across BRD, user-story, planner, budget, and executive-report agents.

All generation uses Agno with Azure OpenAI. Azure OpenAI configuration is required for agent output generation.

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

Missing Azure values, Azure API errors, invalid JSON, or incomplete agent artifacts fail clearly instead of silently using local output.

Endpoints

- `GET /health` - basic health check
- `POST /v1/auth/login` - local demo login for workflow token creation
- `POST /v1/brd/preview` - multipart upload file field `file`; returns structured BRD JSON
- `POST /v1/brd/generate` - JSON body with `fields`; returns a BRD `.docx`
- `POST /v1/brd/download` - JSON BRD preview body; returns a BRD `.docx`
- `POST /v1/userstory/generate-file` - multipart BRD file field `file`; returns backlog JSON
- `POST /v1/userstory/download` - user-story JSON body; returns a `.docx`
- `GET /planer/planner-status` - shows whether Azure OpenAI is configured, without exposing secrets
- `GET /planer/sample-documents` - lists local documents under `sample_docs/`
- `POST /planer/upload` - multipart upload file field `file`; returns generated planner artifacts and review
- `POST /planer/plan-text` - JSON body with `text`; returns generated planner artifacts and review
- `POST /planer/download` - planner JSON body; returns a planner `.docx`
- `POST /v1/budget/generate-from-file` - multipart planner file field `file`; returns budget JSON
- `POST /v1/budget/generate` - JSON planner payload; returns budget JSON
- `POST /v1/budget/download` - budget JSON body; returns a `.docx`
- `POST /v1/executive-report/generate` - multipart files field `files`; returns executive report JSON
- `POST /v1/executive-report/download` - executive report JSON body; returns a `.docx`

Note: This is an initial prototype. Files are stored in `uploads/` and outputs in `outputs/`.

Agent structure
 - Shared upload extraction, JSON helpers, and Word report rendering live in `app/common/`.
 - BRD routes live in `app/brd_agent/route/brd_api.py`; BRD prompts and Agno orchestration live in `app/brd_agent/agent/`.
 - User-story routes live in `app/userstory_agent/route/userstory_api.py`; user-story prompts and Agno orchestration live in `app/userstory_agent/agent/`.
 - Planner routes live in `app/planner_agent/route/planer_api.py`; planner prompts, review, and Agno orchestration live in `app/planner_agent/agent/`.
 - Budget routes live in `app/budget_agent/route/budget_api.py`; budget prompts and Agno orchestration live in `app/budget_agent/agent/`.
 - Executive-report routes live in `app/executive_agent/route/executive_api.py`; executive prompts and Agno orchestration live in `app/executive_agent/agent/`.

Frontend
 - A React frontend (Vite) is in `frontend/`. Run it in a second terminal while the backend is running.
 - The report includes visual charts for schedule, milestones, dependencies, resources, effort, and risks.
 - The generated output has a separate `Quality Scores` tab for input grounding, business accuracy, requirements quality, hallucination control, traceability, stakeholder mapping, risk management, technical accuracy, BRD completeness, and audit readiness.
 - The standalone workflow chain page is available at `http://localhost:3000/workflow`.
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

Open the frontend at `http://localhost:3000`. It expects the backend at `http://localhost:8000`.
To use the hosted Azure backend instead, set `VITE_API_BASE_URL=https://gds-pmoh-demo-be-wa-eus.azurewebsites.net` in `frontend/.env.local`.

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

If the frontend port `3000` is already in use, stop the process using that port.

macOS / Linux:

```bash
lsof -ti :3000
kill -9 $(lsof -ti :3000)
```

Windows PowerShell:

```powershell
netstat -ano | findstr :3000
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

Agno integration
 - The project includes an Agno adapter at `app/planner_agent/agent/agno_adapter.py`.
 - You do not start Agno as a separate server. Start the FastAPI backend; the backend runs the Agno planner pipeline inside the Python process.
 - `agno` is included in `requirements.txt`, so it is installed when you install backend dependencies in `.venv`.
 - To start the backend with Agno available:

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

If `agno` is not installed, the backend fails clearly instead of running a partial planner pipeline. Azure OpenAI is required.

Check OpenAI Usage
 - Start the backend and call:

```bash
curl http://localhost:8000/planer/planner-status
```

Expected when Azure OpenAI is configured:

```json
{
  "azure_openai_configured": true,
  "provider": "agno_azure_openai"
}
```

Debug Upload Failures
 - Watch the backend terminal where `uvicorn` is running. The app logs each stage:
   - upload received
   - upload saved
   - text extraction completed
   - Agno pipeline started
   - generate node started/completed
   - Azure OpenAI request started/completed
   - review node started/completed
   - output saved
 - If upload fails, the frontend shows the backend error message in an `Upload Failed` panel.
 - The upload fails if Azure OpenAI is not configured, Azure returns an error, Agno is unavailable, or the AI response does not include all required planner artifact keys.
 - Generator requests use Agno with Azure OpenAI and strict JSON-only prompts.
 - If the first AI response is invalid JSON or misses required artifact keys, the generator makes one stricter AI repair request. If that also fails, the upload fails instead of rendering incomplete data.
