"""A scheduled, bounded policy for official public claims."""

from __future__ import annotations

from typing import Mapping

from simulation.institutions import InstitutionView, OfficialClaim


class InstitutionPolicy:
    def __init__(self, claim_schedule: Mapping[int, int]) -> None:
        self._claim_schedule = dict(claim_schedule)

    def choose_claim(self, view: InstitutionView) -> OfficialClaim | None:
        value = self._claim_schedule.get(view.tick)
        if value is None:
            return None
        return OfficialClaim(
            proposition="daily_allocation_units",
            asserted_value=value,
        )
