import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.auth.route import router as auth_router
from app.brd_agent.route import router as brd_router
from app.budget_agent.route import router as budget_router
from app.executive_agent.route import router as executive_router
from app.planner_agent.route import router as planner_router
from app.userstory_agent.route import router as userstory_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="PMO Multi-Agent Workflow API")

# Allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(brd_router)
app.include_router(userstory_router)
app.include_router(planner_router)
app.include_router(budget_router)
app.include_router(executive_router)


@app.get("/health")
def health():
    return {"status": "ok"}
