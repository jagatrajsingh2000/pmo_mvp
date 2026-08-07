import logging
from typing import Any, Dict

from app.common.agent_runtime import generate_required_json

from .prompts import USER_STORY_REQUIRED_KEYS, user_story_prompt, user_story_repair_prompt

logger = logging.getLogger(__name__)


def _validate_user_stories(payload: Dict[str, Any]) -> None:
    if not isinstance(payload.get("backlog"), list):
        raise RuntimeError("User Story Agent response backlog must be an array.")
    if not isinstance(payload.get("epics"), list):
        raise RuntimeError("User Story Agent response epics must be an array.")
    if len(payload.get("backlog", [])) < 3:
        raise RuntimeError("User Story Agent response is too shallow: backlog must contain at least 3 stories.")


def generate_user_stories(document_text: str) -> Dict[str, Any]:
    logger.info("User Story agent starting text_chars=%s", len(document_text or ""))
    result = generate_required_json(
        agent_name="userstory_agent",
        prompt=user_story_prompt(document_text),
        required_keys=USER_STORY_REQUIRED_KEYS,
        repair_prompt=lambda invalid, error: user_story_repair_prompt(document_text, invalid, error),
        validator=_validate_user_stories,
        max_tokens=14000,
    )
    logger.info("User Story agent completed stories=%s epics=%s", len(result.get("backlog", [])), len(result.get("epics", [])))
    return result
