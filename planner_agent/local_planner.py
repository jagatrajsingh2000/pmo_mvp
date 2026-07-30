import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from .prompts import ARTIFACT_KEYS

DEFAULT_SPRINT_DAYS = 14


def create_plan(document_text: str) -> Dict[str, Any]:
    clean_text = _normalize(document_text)
    project_name = _field(clean_text, "Project Name") or "Uploaded Project"
    start_date = _project_start(clean_text)
    launch_date = _launch_date(clean_text)
    sprint_days = _sprint_days(clean_text)
    team = _team(clean_text)
    tasks = _tasks(clean_text, start_date, sprint_days)

    plan = {
        "project_name": project_name,
        "planning_mode": "local_deterministic",
        "wbs": _wbs(tasks),
        "project_schedule": tasks,
        "sprint_plan": _sprints(tasks, start_date, sprint_days),
        "milestone_plan": _milestones(start_date, launch_date, tasks),
        "critical_path": _critical_path(tasks),
        "dependency_map": _dependency_map(tasks),
        "resource_allocation": _resource_allocation(team, tasks),
        "timeline_risks": _risks(clean_text, launch_date, tasks),
        "effort_estimation": _effort(tasks),
        "schedule_optimizations": _optimizations(team, launch_date, tasks),
    }

    for key in ARTIFACT_KEYS:
        plan.setdefault(key, [])
    return plan


def review_plan(document_text: str, generated: Dict[str, Any]) -> Dict[str, Any]:
    missing = [key for key in ARTIFACT_KEYS if not generated.get(key)]
    issues = []
    suggestions = []

    if missing:
        issues.append(f"Missing or empty artifact sections: {', '.join(missing)}")
    if not _project_start(document_text):
        suggestions.append("Add a clear project start date.")
    if not _launch_date(document_text):
        suggestions.append("Add milestone or launch deadlines to improve schedule validation.")
    if not _team(document_text):
        suggestions.append("Add team structure and availability for stronger allocation planning.")

    schedule = generated.get("project_schedule") or []
    if schedule and not any(task.get("dependencies") for task in schedule):
        issues.append("No explicit task dependencies were found; critical path is an approximation.")

    return {
        "issues": issues or ["No blocking issues found in the generated first-pass plan."],
        "suggestions": suggestions
        or [
            "Validate durations with engineering and QA leads.",
            "Confirm external dependency dates before baselining the plan.",
        ],
        "confidence": "medium" if issues else "high",
    }


def _normalize(text: str) -> str:
    return re.sub(r"\r\n?", "\n", text or "").strip()


def _field(text: str, label: str) -> Optional[str]:
    match = re.search(rf"^{re.escape(label)}\s*:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def _project_start(text: str) -> date:
    value = _field(text, "Project start date")
    return _parse_date(value) or date.today()


def _launch_date(text: str) -> Optional[date]:
    for label in ("Major launch milestone", "Launch date", "Deadline"):
        value = _field(text, label)
        parsed = _parse_date(value)
        if parsed:
            return parsed
    dates = [_parse_date(item) for item in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text)]
    dates = [item for item in dates if item]
    return max(dates) if dates else None


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    match = re.search(r"\d{4}-\d{2}-\d{2}", value)
    if not match:
        return None
    return datetime.strptime(match.group(0), "%Y-%m-%d").date()


def _sprint_days(text: str) -> int:
    match = re.search(r"Sprint duration\s*:\s*(\d+)\s*(?:weeks?|days?)", text, re.IGNORECASE)
    if not match:
        return DEFAULT_SPRINT_DAYS
    amount = int(match.group(1))
    return amount * 7 if "week" in match.group(0).lower() else amount


def _team(text: str) -> Dict[str, int]:
    roles = {
        "developer": r"(\d+)\s+developers?",
        "qa": r"(\d+)\s+QA",
        "ux_designer": r"(\d+)\s+UX designers?",
        "project_manager": r"(\d+)\s+PM\b",
        "scrum_master": r"(\d+)\s+Scrum Masters?",
    }
    team = {}
    for role, pattern in roles.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            team[role] = int(match.group(1))
    return team


def _tasks(text: str, start: date, sprint_days: int) -> List[Dict[str, Any]]:
    candidates = _bullets_after(text, "Scope") or _bullets_after(text, "Desired Outputs")
    if not candidates:
        candidates = [
            "Ingest project documents",
            "Extract requirements and dependencies",
            "Generate WBS and timeline",
            "Review risks and optimization recommendations",
        ]

    tasks = []
    current_start = start
    for index, candidate in enumerate(candidates[:10], start=1):
        duration = 5 if index <= 2 else 8
        end = _add_work_days(current_start, duration)
        tasks.append(
            {
                "id": f"T{index:02d}",
                "name": _task_name(candidate),
                "duration_days": duration,
                "start_date": current_start.isoformat(),
                "end_date": end.isoformat(),
                "owner_role": _owner_role(candidate),
                "dependencies": [] if index == 1 else [f"T{index - 1:02d}"],
            }
        )
        current_start = end + timedelta(days=1)
    return tasks


def _bullets_after(text: str, heading: str) -> List[str]:
    match = re.search(rf"{re.escape(heading)}\s*:\s*\n(?P<body>(?:[-*]\s+.+\n?)+)", text, re.IGNORECASE)
    if not match:
        return []
    return [line.strip("-* ").strip() for line in match.group("body").splitlines() if line.strip()]


def _task_name(value: str) -> str:
    return value.rstrip(".")


def _owner_role(value: str) -> str:
    lowered = value.lower()
    if "qa" in lowered or "test" in lowered:
        return "qa"
    if "ux" in lowered or "design" in lowered:
        return "ux_designer"
    if "milestone" in lowered or "schedule" in lowered or "plan" in lowered:
        return "project_manager"
    return "developer"


def _add_work_days(start: date, days: int) -> date:
    current = start
    added = 1
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def _wbs(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{"code": f"1.{index}", "task_id": task["id"], "deliverable": task["name"]} for index, task in enumerate(tasks, 1)]


def _sprints(tasks: List[Dict[str, Any]], start: date, sprint_days: int) -> List[Dict[str, Any]]:
    sprints = {}
    for task in tasks:
        task_start = datetime.strptime(task["start_date"], "%Y-%m-%d").date()
        sprint_no = ((task_start - start).days // sprint_days) + 1
        sprints.setdefault(sprint_no, []).append(task["id"])
    return [
        {
            "sprint": sprint_no,
            "start_date": (start + timedelta(days=(sprint_no - 1) * sprint_days)).isoformat(),
            "end_date": (start + timedelta(days=(sprint_no * sprint_days) - 1)).isoformat(),
            "task_ids": task_ids,
        }
        for sprint_no, task_ids in sorted(sprints.items())
    ]


def _milestones(start: date, launch: Optional[date], tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    milestones = [{"name": "Project kickoff", "date": start.isoformat()}]
    if tasks:
        midpoint = tasks[len(tasks) // 2]
        milestones.append({"name": "Plan baseline ready", "date": midpoint["end_date"]})
        milestones.append({"name": "Execution plan complete", "date": tasks[-1]["end_date"]})
    if launch:
        milestones.append({"name": "Launch deadline", "date": launch.isoformat()})
    return milestones


def _critical_path(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "task_ids": [task["id"] for task in tasks],
        "summary": "Sequential dependency chain inferred from the uploaded project scope.",
    }


def _dependency_map(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {"task_id": task["id"], "depends_on": task["dependencies"], "blocks": [next_task["id"]] if index + 1 < len(tasks) else []}
        for index, (task, next_task) in enumerate(zip(tasks, tasks[1:] + [{}]))
    ]


def _resource_allocation(team: Dict[str, int], tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    capacity = team or {"developer": 1, "qa": 1, "project_manager": 1}
    return [
        {
            "role": role,
            "available_count": count,
            "assigned_task_ids": [task["id"] for task in tasks if task["owner_role"] == role],
        }
        for role, count in capacity.items()
    ]


def _risks(text: str, launch: Optional[date], tasks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    risks = [
        {
            "risk": "Dependency details may be incomplete in the source document.",
            "mitigation": "Confirm predecessor and blocker relationships during planning review.",
        }
    ]
    if launch and tasks:
        last_end = datetime.strptime(tasks[-1]["end_date"], "%Y-%m-%d").date()
        if last_end > launch:
            risks.append(
                {
                    "risk": "Generated schedule exceeds the launch deadline.",
                    "mitigation": "Parallelize discovery/build tracks or reduce MVP scope.",
                }
            )
    if "resource availability" in text.lower():
        risks.append(
            {
                "risk": "Resource availability needs calendar-level validation.",
                "mitigation": "Collect holidays, leave plans, and allocation percentages.",
            }
        )
    return risks


def _effort(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = sum(task["duration_days"] for task in tasks)
    return {
        "total_duration_days": total,
        "total_person_days": total,
        "basis": "First-pass estimate from inferred scope items.",
    }


def _optimizations(team: Dict[str, int], launch: Optional[date], tasks: List[Dict[str, Any]]) -> List[str]:
    suggestions = [
        "Run requirements extraction and UX review in parallel where inputs are ready.",
        "Baseline dependencies before sprint planning to reduce rework.",
    ]
    if team.get("qa", 0) <= 1:
        suggestions.append("Shift QA involvement earlier to avoid a single late testing bottleneck.")
    if launch and tasks:
        last_end = datetime.strptime(tasks[-1]["end_date"], "%Y-%m-%d").date()
        if (launch - last_end).days < 10:
            suggestions.append("Add schedule buffer before launch for defect fixes and stakeholder sign-off.")
    return suggestions
