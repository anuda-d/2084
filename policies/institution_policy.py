"""A scheduled, bounded policy for official public claims."""

from __future__ import annotations

from typing import Mapping

from simulation.institutions import (
    InstitutionView,
    OfficialClaim,
    OfficialRecordPublication,
)


class InstitutionPolicy:
    def __init__(
        self,
        claim_schedule: Mapping[int, int],
        *,
        initial_publication_schedule: (
            Mapping[int, OfficialRecordPublication] | None
        ) = None,
    ) -> None:
        self._claim_schedule = dict(claim_schedule)
        self._initial_publication_schedule = dict(initial_publication_schedule or {})

    def choose_initial_publication(
        self, view: InstitutionView
    ) -> OfficialRecordPublication | None:
        return self._initial_publication_schedule.get(view.tick)

    def choose_claim(self, view: InstitutionView) -> OfficialClaim | None:
        value = self._claim_schedule.get(view.tick)
        if value is None:
            return None
        return OfficialClaim(
            proposition="daily_allocation_units",
            asserted_value=value,
        )
