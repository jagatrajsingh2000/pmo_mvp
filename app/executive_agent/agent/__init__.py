"""Azure OpenAI backed executive report agent implementation."""

from .agents import generate_executive_report
from .agno_adapter import run_executive_pipeline_agno

__all__ = ["generate_executive_report", "run_executive_pipeline_agno"]
