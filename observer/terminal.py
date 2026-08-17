"""Filtered, focal-character terminal presentation."""

from __future__ import annotations

from typing import Iterable

from simulation.engine import FocalSnapshot


def _location_label(location: str) -> str:
    return location.replace("_", " ").title()


def _units(value: int, *, allocation: bool = False) -> str:
    noun = "allocation unit" if allocation else "unit"
    if value != 1:
        noun += "s"
    return f"{value} {noun}"


def _observation_line(snapshot: FocalSnapshot, index: int) -> str | None:
    observation = snapshot.new_observations[index]
    details = observation.details
    kind = details.get("evidence_kind")
    if kind == "arrival":
        return f"Observed: arrived at {_location_label(details['destination'])}."
    if kind == "work_completed":
        return "Observed: completed the scheduled ledger work."
    if kind == "visible_supporting_action":
        return "Visible nearby: a co-worker completed their scheduled work."
    if kind == "direct_resource_claim":
        return (
            "Observed: directly saw "
            f"{_units(details['asserted_value'], allocation=True)}."
        )
    if kind == "official_resource_claim":
        verb = "revised its claim to" if details.get("revises_event_id") else "claimed"
        return (
            f"Observed: official broadcast {verb} "
            f"{_units(details['asserted_value'], allocation=True)}."
        )
    if kind == "official_record_version":
        return (
            "Official schedule encountered: weekly household entitlement is "
            f"{details['asserted_value']} packets."
        )
    if kind == "allocation_outcome":
        return (
            "Physical handover: "
            f"{details['granted_units']} packets received and "
            f"{details['unfilled_units']} packet unfilled."
        )
    if kind == "social_pressure":
        if details.get("proposition") == "weekly_household_ration_entitlement_packets":
            return (
                "Public pressure: the allocation clerk repeated the official "
                f"{details['asserted_value']}-packet entitlement under "
                f"{details['reason']}."
            )
        return (
            "Public pressure: the allocation clerk repeated the official "
            f"{details['asserted_value']}-unit claim under {details['reason']}."
        )
    if kind == "diary_write_completed":
        return (
            "Diary write completed: retained the private "
            f"{details['asserted_value']}-unit perspective."
        )
    if kind == "diary_read_completed":
        return (
            "Diary read returned the earlier "
            f"{details['asserted_value']}-unit perspective."
        )
    return None


def render_terminal(snapshots: Iterable[FocalSnapshot]) -> str:
    """Render only fields already admitted to the focal projection."""
    snapshots = tuple(snapshots)
    lines = [
        "2084 — FIRST LIVING SLICE",
        "Normal observer: focal-character knowledge only",
    ]
    for snapshot in snapshots:
        reason = snapshot.explanation.rstrip(".") + "."
        lines.extend(
            (
                "",
                f"Tick {snapshot.tick:02d} | {_location_label(snapshot.location)}",
                f"Aim: {snapshot.aim}",
                f"Action: {snapshot.current_action}",
                f"Reason: {reason}",
            )
        )
        for index in range(len(snapshot.new_observations)):
            line = _observation_line(snapshot, index)
            if line is not None:
                lines.append(line)
        for result in snapshot.new_action_results:
            if result.status == "rejected" and result.reason:
                lines.append("Action rejected: " + result.reason.rstrip(".") + ".")
        if snapshot.held_units > 0:
            lines.append(
                "Household allocation: "
                f"{snapshot.held_units} held; "
                f"{snapshot.remaining_required_units} still needed."
            )
        private = next(
            (belief for belief in reversed(snapshot.beliefs) if belief.context == "private"),
            None,
        )
        public = next(
            (belief for belief in reversed(snapshot.beliefs) if belief.context == "public"),
            None,
        )
        if private is not None:
            uncertainty = "; conflicts with a public claim" if private.conflicts_with else ""
            lines.append(
                f"Private belief: {_units(private.asserted_value)} "
                f"({private.confidence:.0%} confidence{uncertainty})."
            )
        if public is not None:
            lines.append(
                f"Public claim retained as a claim: {_units(public.asserted_value)} "
                f"({public.confidence:.0%} confidence)."
            )
    return "\n".join(lines) + "\n"
