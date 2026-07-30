# PMO Timeline Planner Agent (FastAPI)

FastAPI + React app that accepts project documents (PDF, XLSX, CSV, DOCX, TXT), extracts text locally, and generates PMO timeline artifacts: WBS, project schedule, sprint plan, milestone plan, critical path, dependency map, resource allocation, timeline risks, effort estimates, and schedule optimization recommendations.

The planner uses Azure OpenAI when `.env` is configured. If Azure values are missing or the call fails, it falls back to a deterministic local planner so the app remains testable with the included sample documents.

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

Configure Azure OpenAI values in `.env` when you want AI-generated plans. If `.env` is empty, the backend still runs with the local deterministic planner for sample testing.

Endpoints

- `GET /health` - basic health check
- `GET /sample-documents` - lists local documents under `sample_docs/`
- `POST /upload` - multipart upload file field `file`; returns generated planner artifacts and review
- `POST /plan-text` - JSON body with `text`; returns generated planner artifacts and review

Note: This is an initial prototype. Files are stored in `uploads/` and outputs in `outputs/`.

Planner agent
 - AI and deterministic planning code is in `planner_agent/` separated from the FastAPI service.
 - Shared prompt contracts live in `planner_agent/prompts.py` to keep generation and review DRY.
 - Local fallback logic lives in `planner_agent/local_planner.py` for repeatable sample testing.

Frontend
 - A React frontend (Vite) is in `frontend/`. Run it in a second terminal while the backend is running.

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
 - For scanned PDFs, the backend uses `pytesseract` + `pdf2image` as a fallback OCR method.
 - You must install the Tesseract binary on your system. On macOS:

```bash
brew install tesseract
```

LangGraph integration
 - The project includes a LangGraph adapter at `planner_agent/langraph_adapter.py`.
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

If `langgraph` is not installed, the app falls back to the internal pipeline implementation. If Azure OpenAI values are missing from `.env`, LangGraph still runs but uses the local deterministic planner nodes.
