import re
from typing import Any, Dict, Iterable, Optional, Tuple

DEFAULT_HOURLY_RATE_USD = 36.0
HOURS_PER_PERSON_DAY = 8.0
HOURS_PER_WEEK = 40.0

DEFAULT_RATE_NOTE = (
    "Actual rate not provided in source; calculated using the standard budget rate "
    "of USD 36/hour."
)

MISSING_TEXT = {
    "",
    "n/a",
    "na",
    "none",
    "null",
    "not specified",
    "not provided",
    "not provided in source",
    "tbd",
}


def apply_standard_hourly_rate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Apply the budget agent's standard labor rate when source rates are missing.

    This is not a content fallback. Azure still generates the budget structure; this
    only prevents zero-cost labor estimates when effort exists but rates are absent.
    """
    if not isinstance(payload, dict):
        return payload

    workstream_total, workstream_defaulted = _normalize_workstreams(payload.get("workstream_estimates"))
    resource_total, resource_defaulted = _normalize_resources(payload.get("resource_costs"))
    timeline_total, timeline_defaulted = _normalize_timeline(
        payload.get("timeline_budget"),
        payload.get("workstream_estimates"),
    )

    computed_total = _first_positive(workstream_total, resource_total, timeline_total)
    defaulted = workstream_defaulted or resource_defaulted or timeline_defaulted
    _normalize_summary(payload, computed_total, defaulted)

    if computed_total > 0 and _is_missing(payload.get("currency")):
        payload["currency"] = "USD"

    return payload


def _normalize_workstreams(workstreams: Any) -> Tuple[float, bool]:
    if not isinstance(workstreams, list):
        return 0.0, False

    total = 0.0
    defaulted = False
    for item in _dict_items(workstreams):
        person_days = _number(item.get("person_days"))
        effort_hours = _number(_first_present(item.get("effort_hours"), item.get("hours"), item.get("total_hours")))

        if person_days <= 0 and effort_hours > 0:
            person_days = effort_hours / HOURS_PER_PERSON_DAY
            item["person_days"] = _format_number(person_days)

        cost = _number(_first_present(item.get("cost"), item.get("estimated_cost"), item.get("total_cost")))
        if cost <= 0 and person_days > 0:
            cost = person_days * HOURS_PER_PERSON_DAY * DEFAULT_HOURLY_RATE_USD
            item["cost"] = _format_money(cost)
            item["assumptions"] = _append_note(item.get("assumptions"), DEFAULT_RATE_NOTE)
            defaulted = True

        total += _number(_first_present(item.get("cost"), item.get("estimated_cost"), item.get("total_cost")))

    return total, defaulted


def _normalize_resources(resources: Any) -> Tuple[float, bool]:
    if not isinstance(resources, list):
        return 0.0, False

    total = 0.0
    defaulted = False
    for item in _dict_items(resources):
        estimated_cost = _number(_first_present(item.get("estimated_cost"), item.get("cost"), item.get("total_cost")))
        count = _number(item.get("count"), average_range=True)
        duration_weeks = _number(
            _first_present(item.get("duration_weeks"), item.get("weeks"), item.get("duration")),
            average_range=True,
        )

        if estimated_cost <= 0 and count > 0 and duration_weeks > 0:
            estimated_cost = count * duration_weeks * HOURS_PER_WEEK * DEFAULT_HOURLY_RATE_USD
            item["estimated_cost"] = _format_money(estimated_cost)
            item["rate_assumption"] = _append_note(item.get("rate_assumption"), DEFAULT_RATE_NOTE)
            defaulted = True

        total += _number(_first_present(item.get("estimated_cost"), item.get("cost"), item.get("total_cost")))

    return total, defaulted


def _normalize_timeline(timeline_budget: Any, workstreams: Any) -> Tuple[float, bool]:
    if not isinstance(timeline_budget, list):
        return 0.0, False

    workstream_costs = _workstream_costs(workstreams)
    total = 0.0
    defaulted = False
    for item in _dict_items(timeline_budget):
        estimated_cost = _number(_first_present(item.get("estimated_cost"), item.get("cost"), item.get("total_cost")))
        if estimated_cost <= 0:
            phase = str(item.get("phase") or item.get("workstream") or "").lower()
            matched_cost = _matching_workstream_cost(phase, workstream_costs)
            if matched_cost > 0:
                estimated_cost = matched_cost
                item["estimated_cost"] = _format_money(estimated_cost)
                item["cost_driver"] = _append_note(
                    item.get("cost_driver"),
                    "Cost aligned to matching workstream labor estimate.",
                )
                defaulted = True
        total += _number(_first_present(item.get("estimated_cost"), item.get("cost"), item.get("total_cost")))

    return total, defaulted


def _normalize_summary(payload: Dict[str, Any], computed_total: float, defaulted: bool) -> None:
    summary = payload.get("cost_summary")
    if not isinstance(summary, dict):
        return

    existing_total = _number(summary.get("total_estimated_cost"))
    if existing_total <= 0 and computed_total > 0:
        summary["total_estimated_cost"] = _format_money(computed_total)
        defaulted = True

    if defaulted:
        summary["basis"] = _append_note(summary.get("basis"), DEFAULT_RATE_NOTE)


def _workstream_costs(workstreams: Any) -> Dict[str, float]:
    if not isinstance(workstreams, list):
        return {}
    costs: Dict[str, float] = {}
    for item in _dict_items(workstreams):
        name = str(item.get("workstream") or "").strip().lower()
        cost = _number(_first_present(item.get("cost"), item.get("estimated_cost"), item.get("total_cost")))
        if name and cost > 0:
            costs[name] = cost
    return costs


def _matching_workstream_cost(phase: str, workstream_costs: Dict[str, float]) -> float:
    if not phase:
        return 0.0
    for name, cost in workstream_costs.items():
        if name in phase or phase in name:
            return cost
    return 0.0


def _dict_items(items: Iterable[Any]) -> Iterable[Dict[str, Any]]:
    for item in items:
        if isinstance(item, dict):
            yield item


def _first_positive(*values: float) -> float:
    for value in values:
        if value > 0:
            return value
    return 0.0


def _first_present(*values: Any) -> Optional[Any]:
    for value in values:
        if not _is_missing(value):
            return value
    return None


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in MISSING_TEXT
    return False


def _number(value: Any, *, average_range: bool = False) -> float:
    if value is None or isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return 0.0

    text = value.strip().replace(",", "")
    if not text:
        return 0.0

    if average_range:
        range_match = re.search(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)", text)
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            return (low + high) / 2

    number_match = re.search(r"\d+(?:\.\d+)?", text)
    if not number_match:
        return 0.0
    return float(number_match.group(0))


def _append_note(existing: Any, note: str) -> str:
    if _is_missing(existing):
        return note

    text = str(existing).strip()
    if note.lower() in text.lower():
        return text
    return f"{text} {note}"


def _format_money(value: float) -> int | float:
    rounded = round(value, 2)
    if rounded.is_integer():
        return int(rounded)
    return rounded


def _format_number(value: float) -> int | float:
    rounded = round(value, 2)
    if rounded.is_integer():
        return int(rounded)
    return rounded
